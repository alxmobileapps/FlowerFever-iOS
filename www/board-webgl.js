/* Live puzzle and celebration renderer. Paths are tessellated into triangles;
   the GPU shades them and composites them with cached image and text textures. */
window.createFlowerBoardRenderer = function (canvas, overlay = false) {
  const surface = document.createElement("canvas");
  const fallback = () => {
    const ctx = canvas.getContext("2d");
    canvas.dataset.renderer = "canvas2d";
    return { get ctx() { return ctx; }, begin() {}, end() {}, clip(path) { ctx.clip(path); } };
  };
  if (new URLSearchParams(location.search).get("boardRenderer") === "2d") return fallback();
  let gl;
  try { gl = surface.getContext("webgl", { alpha: true, stencil: true, antialias: true }); }
  catch (_) { return fallback(); }
  if (!gl || !gl.getContextAttributes().stencil) return fallback();

  function shader(type, source) {
    const id = gl.createShader(type);
    gl.shaderSource(id, source);
    gl.compileShader(id);
    if (!gl.getShaderParameter(id, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(id));
    return id;
  }
  const program = gl.createProgram();
  try {
    gl.attachShader(program, shader(gl.VERTEX_SHADER, `
      precision mediump float;
      attribute vec2 point, uvIn;
      attribute vec4 colorIn;
      uniform vec2 size;
      varying vec2 uv, position;
      varying vec4 color;
      void main() {
        position = point;
        uv = uvIn;
        color = colorIn;
        vec2 p = point / size;
        gl_Position = vec4(2.0*p.x-1.0, 1.0-2.0*p.y, 0.0, 1.0);
      }`));
    gl.attachShader(program, shader(gl.FRAGMENT_SHADER, `
      precision mediump float;
      varying vec2 uv, position;
      varying vec4 color;
      uniform sampler2D image;
      uniform int mode;
      uniform vec3 inverseX, inverseY;
      uniform vec4 endpoints;
      uniform vec2 radii;
      uniform vec4 stops[6];
      uniform vec4 offsetsA;
      uniform vec2 offsetsB;
      float ramp(float t, float a, float b) { return clamp((t-a)/max(0.00001,b-a),0.0,1.0); }
      void main() {
        if (mode == 1) {
          gl_FragColor = texture2D(image, uv) * color.a;
        } else if (mode == 2 || mode == 3) {
          vec3 p = vec3(position, 1.0);
          vec2 v = vec2(dot(inverseX,p), dot(inverseY,p)) - endpoints.xy;
          vec2 d = endpoints.zw - endpoints.xy;
          float t;
          if (mode == 2) {
            t = dot(v,d) / max(0.00001,dot(d,d));
          } else {
            float dr = radii.y-radii.x;
            float a = dot(d,d)-dr*dr;
            float b = dot(v,d)+radii.x*dr;
            float c = dot(v,v)-radii.x*radii.x;
            float det = max(0.0,b*b-a*c);
            t = abs(a) < 0.00001 ? c / max(0.00001,2.0*b) : (b-sqrt(det))/a;
          }
          vec4 g = stops[0];
          g = mix(g, stops[1], ramp(t, offsetsA.x, offsetsA.y));
          g = mix(g, stops[2], ramp(t, offsetsA.y, offsetsA.z));
          g = mix(g, stops[3], ramp(t, offsetsA.z, offsetsA.w));
          g = mix(g, stops[4], ramp(t, offsetsA.w, offsetsB.x));
          g = mix(g, stops[5], ramp(t, offsetsB.x, offsetsB.y));
          gl_FragColor = vec4(g.rgb * g.a, g.a) * color.a;
        } else {
          gl_FragColor = vec4(color.rgb * color.a, color.a);
        }
      }`));
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(program));
  } catch (err) {
    console.warn("Flower Fever WebGL unavailable", err);
    return fallback();
  }

  const buffer = gl.createBuffer();
  gl.useProgram(program);
  gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
  for (const [name, count, offset] of [["point", 2, 0], ["uvIn", 2, 8], ["colorIn", 4, 16]]) {
    const index = gl.getAttribLocation(program, name);
    gl.enableVertexAttribArray(index);
    gl.vertexAttribPointer(index, count, gl.FLOAT, false, 32, offset);
  }
  const u = Object.fromEntries(["size", "image", "mode", "inverseX", "inverseY", "endpoints", "radii", "stops[0]", "offsetsA", "offsetsB"]
    .map(name => [name, gl.getUniformLocation(program, name)]));
  gl.uniform1i(u.image, 0);
  gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, true);
  const emptyTexture = gl.createTexture();
  gl.bindTexture(gl.TEXTURE_2D, emptyTexture);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array([255,255,255,255]));
  gl.enable(gl.BLEND);
  gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);

  const textureCache = new Map(), labelCache = new Map(), colorCache = new Map();
  const white = [1, 1, 1, 1];
  let vertices = [], batchTexture = null, clipDepth = 0, layoutKey, state, path, subpath;
  const stack = [];
  const identity = () => new DOMMatrix();
  const initial = () => ({ m: identity(), globalAlpha: 1, fillStyle: "#000", strokeStyle: "#000",
    lineWidth: 1, lineCap: "butt", lineJoin: "miter", dash: [], font: "10px sans-serif",
    textAlign: "start", textBaseline: "alphabetic", shadowBlur: 0, shadowColor: "transparent" });
  state = initial();
  path = [];

  function color(value) {
    if (colorCache.has(value)) return colorCache.get(value);
    let c = [0, 0, 0, 1];
    if (value[0] === "#") {
      let hex = value.slice(1);
      if (hex.length <= 4) hex = [...hex].map(x => x + x).join("");
      if (hex.length === 6) hex += "ff";
      c = hex.match(/../g).map(x => parseInt(x, 16) / 255);
    } else if (/^rgba?\(/.test(value)) {
      const [r, g, b, a = 1] = value.slice(value.indexOf("(") + 1, -1).split(",").map(Number);
      c = [r / 255, g / 255, b / 255, Math.max(0, Math.min(1, a))];
    } else if (/^hsla?\(/.test(value)) {
      const [h, s, l, a = 1] = value.match(/-?[\d.]+(?:e[+-]?\d+)?/gi).map(Number);
      const light = l / 100, amp = s / 100 * Math.min(light, 1 - light);
      const channel = n => {
        const k = ((n + h / 30) % 12 + 12) % 12;
        return light - amp * Math.max(-1, Math.min(k - 3, 9 - k, 1));
      };
      c = [channel(0), channel(8), channel(4), a];
    } else if (value === "white") c = white;
    else if (value === "transparent") c[3] = 0;
    if (colorCache.size > 1024) colorCache.clear();
    colorCache.set(value, c);
    return c;
  }
  function point(x, y, m = state.m) { return [m.a*x + m.c*y + m.e, m.b*x + m.d*y + m.f]; }
  function vertex(p, c, alpha, uv = [0, 0]) {
    vertices.push(p[0], p[1], uv[0], uv[1], c[0], c[1], c[2], c[3]*alpha);
  }
  function submit(mode) {
    if (!vertices.length) return;
    gl.uniform1i(u.mode, mode);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(vertices), gl.STREAM_DRAW);
    gl.drawArrays(gl.TRIANGLES, 0, vertices.length / 8);
    vertices = [];
  }
  function flush() {
    gl.bindTexture(gl.TEXTURE_2D, batchTexture || emptyTexture);
    submit(batchTexture ? 1 : 0);
    batchTexture = null;
  }
  function textured(source, x, y, w, h) {
    if (!source?.width || !source.height) return;
    let tex = textureCache.get(source);
    if (!tex || batchTexture !== tex) flush();
    if (!tex) {
      if (textureCache.size >= 160) {
        const oldest = textureCache.keys().next().value;
        gl.deleteTexture(textureCache.get(oldest));
        textureCache.delete(oldest);
      }
      tex = gl.createTexture();
      gl.bindTexture(gl.TEXTURE_2D, tex);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, source);
    }
    textureCache.delete(source);
    textureCache.set(source, tex);
    batchTexture = tex;
    for (const uv of [[0,0],[1,0],[0,1],[0,1],[1,0],[1,1]]) {
      vertex(point(x+w*uv[0], y+h*uv[1]), white, state.globalAlpha, uv);
    }
  }

  function gradient(mode, x, y, x2, y2, r = 0, r2 = 0) {
    // Use device-normalized gradient coordinates to avoid overflowing mediump
    // arithmetic on large boards and during full-screen effects.
    const unit = Math.max(1e-4, Math.abs(x2-x), Math.abs(y2-y), r, r2);
    const m = state.m.inverse();
    return { mode, inverseX: [m.a/unit,m.c/unit,(m.e-x)/unit], inverseY: [m.b/unit,m.d/unit,(m.f-y)/unit],
      endpoints: [0,0,(x2-x)/unit,(y2-y)/unit], radii: [r/unit,r2/unit], stops: [],
      addColorStop(offset, c) { this.stops.push([offset,color(c)]); } };
  }
  function mesh(triangles, style) {
    if (!triangles.length) return;
    if (batchTexture || typeof style !== "string") flush();
    if (typeof style === "string") {
      const c = color(style);
      for (const p of triangles) vertex(p,c,state.globalAlpha);
      return;
    }
    const stops = style.stops.slice(0,6).sort((a,b) => a[0]-b[0]);
    if (!stops.length) return;
    while (stops.length < 6) stops.push(stops[stops.length-1]);
    gl.bindTexture(gl.TEXTURE_2D, emptyTexture);
    gl.uniform3fv(u.inverseX,style.inverseX);
    gl.uniform3fv(u.inverseY,style.inverseY);
    gl.uniform4fv(u.endpoints,style.endpoints);
    gl.uniform2fv(u.radii,style.radii);
    gl.uniform4fv(u["stops[0]"],stops.flatMap(s => s[1]));
    gl.uniform4fv(u.offsetsA,stops.slice(0,4).map(s => s[0]));
    gl.uniform2fv(u.offsetsB,stops.slice(4).map(s => s[0]));
    for (const p of triangles) vertex(p,white,state.globalAlpha);
    submit(style.mode);
  }

  const cross = (a,b,c) => (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]);
  function triangulate(points, out) {
    const p = points.filter((v,i) => i === 0 || Math.hypot(v[0]-points[i-1][0],v[1]-points[i-1][1]) > .001);
    if (p.length > 2 && Math.hypot(p[0][0]-p.at(-1)[0],p[0][1]-p.at(-1)[1]) < .001) p.pop();
    if (p.length < 3) return;
    let area = 0;
    for (let i=0;i<p.length;i++) area += cross([0,0],p[i],p[(i+1)%p.length]);
    const sign = Math.sign(area);
    if (!sign) return;
    if (p.every((v,i) => sign*cross(p[(i+p.length-1)%p.length],v,p[(i+1)%p.length]) >= -.0001)) {
      for (let i=1;i+1<p.length;i++) out.push(p[0],p[i],p[i+1]);
      return;
    }
    while (p.length > 2) {
      let ear = false;
      for (let i=0;i<p.length;i++) {
        const prev=(i+p.length-1)%p.length, next=(i+1)%p.length, a=p[prev], b=p[i], c=p[next];
        const turn = sign*cross(a,b,c);
        if (turn < -.0001) continue;
        if (turn > .0001 && p.some((v,j) => j!==prev && j!==i && j!==next &&
          sign*cross(a,b,v)>.0001 && sign*cross(b,c,v)>.0001 && sign*cross(c,a,v)>.0001)) continue;
        if (turn > .0001) out.push(a,b,c);
        p.splice(i,1);
        ear=true;
        break;
      }
      if (!ear) break;
    }
  }
  function pathMesh() {
    const out=[];
    for (const part of path) triangulate(part.points,out);
    return out;
  }
  function rect(out, x, y, w, h, m = state.m) {
    const a=point(x,y,m), b=point(x+w,y,m), c=point(x,y+h,m), d=point(x+w,y+h,m);
    out.push(a,b,c,c,b,d);
    return out;
  }
  function stencil(triangles, add) {
    flush();
    gl.enable(gl.STENCIL_TEST);
    gl.stencilFunc(gl.EQUAL,clipDepth,255);
    gl.stencilOp(gl.KEEP,gl.KEEP,add ? gl.INCR : gl.DECR);
    gl.colorMask(false,false,false,false);
    for (const p of triangles) vertex(p,white,1);
    submit(0);
    gl.colorMask(true,true,true,true);
    clipDepth += add ? 1 : -1;
    gl.stencilOp(gl.KEEP,gl.KEEP,gl.KEEP);
    gl.stencilFunc(gl.EQUAL,clipDepth,255);
    if (!clipDepth) gl.disable(gl.STENCIL_TEST);
  }

  function ellipse(x,y,rx,ry,rotation,start,end,ccw = false) {
    const tau=Math.PI*2;
    let span=end-start;
    if (Math.abs(span)>=tau) span=ccw ? -tau : tau;
    else if (ccw ? span>0 : span<0) span+=ccw ? -tau : tau;
    const m=state.m, radius=Math.max(rx,ry)*Math.max(Math.hypot(m.a,m.b),Math.hypot(m.c,m.d));
    const n=Math.max(2,Math.min(64,Math.ceil(Math.abs(span)*Math.sqrt(Math.max(1,radius)))));
    const cs=Math.cos(rotation), sn=Math.sin(rotation);
    for(let i=0;i<=n;i++){
      const a=start+span*i/n, u=rx*Math.cos(a), v=ry*Math.sin(a);
      ctx.lineTo(x+cs*u-sn*v,y+sn*u+cs*v);
    }
  }
  function strokeMesh(width, dash) {
    const out=[];
    const cap=(p,r) => {
      for (let i=0;i<8;i++) {
        const a=i*Math.PI/4,b=(i+1)*Math.PI/4;
        out.push(p,[p[0]+r*Math.cos(a),p[1]+r*Math.sin(a)],[p[0]+r*Math.cos(b),p[1]+r*Math.sin(b)]);
      }
    };
    const segment=(a,b,roundStart,roundEnd) => {
      const dx=b[0]-a[0],dy=b[1]-a[1],len=Math.hypot(dx,dy);
      if(len<.001)return;
      const x=-dy/len*width,y=dx/len*width;
      const p=[a[0]+x,a[1]+y],q=[a[0]-x,a[1]-y],r=[b[0]+x,b[1]+y],s=[b[0]-x,b[1]-y];
      out.push(p,q,r,r,q,s);
      if(roundStart)cap(a,width);
      if(roundEnd)cap(b,width);
    };
    for (const {points,closed} of path) {
      const n=points.length;
      if(n<2)continue;
      const count=closed?n:n-1;
      let j=0,remaining=dash[0];
      for(let i=0;i<count;i++){
        const a=points[i],b=points[(i+1)%n];
        if (!dash.length) {
          segment(a,b,!closed && i===0 && state.lineCap==="round",
            i===count-1 && !closed && state.lineCap==="round");
          if (i<count-1 || closed) {
            const c=points[(i+2)%n];
            const dx=b[0]-a[0],dy=b[1]-a[1],ex=c[0]-b[0],ey=c[1]-b[1];
            const d=Math.hypot(dx,dy),e=Math.hypot(ex,ey);
            if(d>.001 && e>.001){
              const side=Math.sign(dy*ex-dx*ey)*width;
              out.push(b,[b[0]-dy/d*side,b[1]+dx/d*side],[b[0]-ey/e*side,b[1]+ex/e*side]);
            }
          }
          continue;
        }
        const len=Math.hypot(b[0]-a[0],b[1]-a[1]);
        const at = d => [a[0]+(b[0]-a[0])*d/len,a[1]+(b[1]-a[1])*d/len];
        for(let pos=0;pos<len-.001;){
          const step=Math.min(remaining,len-pos);
          if(j%2===0)segment(at(pos),at(pos+step),state.lineCap==="round",state.lineCap==="round");
          pos+=step;
          remaining-=step;
          if(remaining<.001){ j=(j+1)%dash.length;remaining=dash[j]; }
        }
      }
    }
    return out;
  }

  function label(text,x,y,stroke) {
    const key=JSON.stringify([text,state.font,state.textAlign,state.textBaseline,stroke,state.lineWidth,
      stroke?state.strokeStyle:state.fillStyle]);
    let cached=labelCache.get(key);
    if(!cached){
      // Glyphs are assets: generate a small label once, then animate its texture.
      const img=document.createElement("canvas"), g=img.getContext("2d");
      g.font=state.font;
      const metrics=g.measureText(text), fontSize=parseFloat(state.font.match(/[\d.]+px/)?.[0] || "10");
      const w=Math.ceil(metrics.width+state.lineWidth*2+6), h=Math.ceil(fontSize*2+state.lineWidth*2+6);
      img.width=w*2; img.height=h*2;
      g.scale(2,2);
      for(const k of ["font","textAlign","textBaseline","lineWidth","strokeStyle","fillStyle"])g[k]=state[k];
      g.lineJoin="round";
      const ox=state.textAlign==="center"?w/2:state.textAlign==="right"||state.textAlign==="end"?w-state.lineWidth-3:state.lineWidth+3;
      const oy=state.textBaseline==="top"?state.lineWidth+3:h/2;
      if(stroke)g.strokeText(text,ox,oy);else g.fillText(text,ox,oy);
      cached={img,w,h,ox,oy};
      if(labelCache.size>=96)labelCache.delete(labelCache.keys().next().value);
      labelCache.set(key,cached);
    }
    textured(cached.img,x-cached.ox,y-cached.oy,cached.w,cached.h);
  }

  const commands={
    setTransform(a,b,c,d,e,f){state.m=new DOMMatrix([a,b,c,d,e,f]);},
    translate(x,y){state.m=state.m.translate(x,y);},
    rotate(a){state.m=state.m.rotate(a*180/Math.PI);},
    scale(x,y){state.m=state.m.scale(x,y);},
    save(){stack.push({state:{...state},clipDepth});},
    restore(){
      const last=stack.pop();
      if(!last)return;
      while(clipDepth>last.clipDepth)stencil(rect([],0,0,surface.width,surface.height,identity()),false);
      state=last.state;
    },
    beginPath(){path=[];subpath=null;},
    moveTo(x,y){subpath={points:[point(x,y)],closed:false};path.push(subpath);},
    lineTo(x,y){if(!subpath)commands.moveTo(x,y);else subpath.points.push(point(x,y));},
    closePath(){if(subpath)subpath.closed=true;},
    quadraticCurveTo(x,y,u,v){
      const b=point(x,y),c=point(u,v),a=subpath?.points.at(-1) || b;
      if(!subpath){subpath={points:[a],closed:false};path.push(subpath);}
      for(let i=1;i<=8;i++){const t=i/8,k=1-t;subpath.points.push([k*k*a[0]+2*k*t*b[0]+t*t*c[0],k*k*a[1]+2*k*t*b[1]+t*t*c[1]]);}
    },
    bezierCurveTo(x,y,u,v,j,k){
      const b=point(x,y),c=point(u,v),d=point(j,k),a=subpath?.points.at(-1) || b;
      if(!subpath){subpath={points:[a],closed:false};path.push(subpath);}
      for(let i=1;i<=10;i++){const t=i/10,k=1-t;subpath.points.push([0,1].map(n=>k*k*k*a[n]+3*k*k*t*b[n]+3*k*t*t*c[n]+t*t*t*d[n]));}
    },
    arc(x,y,r,a,b,ccw){ellipse(x,y,r,r,0,a,b,ccw);},
    ellipse,
    arcTo(x,y,u,v,r){
      const last=subpath?.points.at(-1);
      if(!last || !r){commands.lineTo(x,y);return;}
      const a=point(...last,state.m.inverse()), dx=a[0]-x,dy=a[1]-y,ex=u-x,ey=v-y;
      const d=Math.hypot(dx,dy),e=Math.hypot(ex,ey);
      if(d<1e-6||e<1e-6){commands.lineTo(x,y);return;}
      const bx=dx/d,by=dy/d,cx=ex/e,cy=ey/e,turn=bx*cy-by*cx;
      if(Math.abs(turn)<1e-6){commands.lineTo(x,y);return;}
      const angle=Math.acos(Math.max(-1,Math.min(1,bx*cx+by*cy)));
      const t=r/Math.tan(angle/2), sx=x+bx*t,sy=y+by*t;
      const sign=Math.sign(turn),hx=sx-sign*by*r,hy=sy+sign*bx*r;
      ellipse(hx,hy,r,r,0,Math.atan2(sy-hy,sx-hx),Math.atan2(y+cy*t-hy,x+cx*t-hx),turn>0);
    },
    fill(){mesh(pathMesh(),state.fillStyle);},
    stroke(){
      const scale=Math.sqrt(Math.abs(state.m.a*state.m.d-state.m.b*state.m.c));
      const dash=state.dash.map(d=>Math.max(.001,d*scale));
      if(state.shadowBlur>0 && state.shadowColor!=="transparent"){
        const opacity=state.globalAlpha;
        state.globalAlpha*=.22;
        mesh(strokeMesh((state.lineWidth/2+state.shadowBlur*.35)*scale,dash),state.shadowColor);
        state.globalAlpha=opacity;
      }
      mesh(strokeMesh(state.lineWidth*scale/2,dash),state.strokeStyle);
    },
    fillRect(x,y,w,h){mesh(rect([],x,y,w,h),state.fillStyle);},
    clip(){stencil(pathMesh(),true);},
    setLineDash(dash){state.dash=dash.length%2 ? dash.concat(dash) : dash.slice();},
    createLinearGradient(x,y,u,v){return gradient(2,x,y,u,v);},
    createRadialGradient(x,y,r,u,v,r2){return gradient(3,x,y,u,v,r,r2);},
    drawImage: textured,
    fillText(t,x,y){label(t,x,y,false);},
    strokeText(t,x,y){label(t,x,y,true);},
    clearRect(){vertices=[];batchTexture=null;gl.clear(gl.COLOR_BUFFER_BIT);}
  };
  const ctx=new Proxy(commands,{
    get(target,key){return Object.hasOwn(target,key)?target[key]:state[key];},
    set(_target,key,value){state[key]=value;return true;}
  });
  canvas.dataset.renderer = "webgl";
  surface.setAttribute("aria-hidden","true");
  surface.dataset.boardRenderer="webgl";
  Object.assign(surface.style, overlay
    ? {position:"fixed",inset:"0",width:"100%",height:"100%",zIndex:"6",pointerEvents:"none"}
    : {position:"absolute",pointerEvents:"none"});
  canvas.after(surface);
  canvas.style.opacity="0";
  let recovery;
  surface.addEventListener("webglcontextlost", () => {
    surface.remove();
    canvas.style.opacity="";
    recovery=fallback();
  }, {once:true});
  let maskRef, maskCell, maskTriangles;
  return {
    get ctx(){return recovery?.ctx || ctx;},
    begin(){
      if(recovery)return;
      const key=[canvas.width,canvas.height,canvas.style.width,canvas.style.height,canvas.style.transform].join(":");
      if(key!==layoutKey){
        layoutKey=key;
        surface.width=canvas.width;surface.height=canvas.height;
        if(!overlay){
          surface.style.left=canvas.offsetLeft+"px";surface.style.top=canvas.offsetTop+"px";
          surface.style.width=canvas.style.width;surface.style.height=canvas.style.height;
          surface.style.transform=canvas.style.transform;
        }
        gl.viewport(0,0,surface.width,surface.height);
        gl.uniform2f(u.size,surface.width,surface.height);
      }
      vertices=[];batchTexture=null;clipDepth=0;stack.length=0;state=initial();
      commands.beginPath();
      gl.disable(gl.STENCIL_TEST);
      gl.clear(gl.COLOR_BUFFER_BIT|gl.STENCIL_BUFFER_BIT);
    },
    clip(nativePath,mask,cell){
      if(recovery){recovery.clip(nativePath);return;}
      if(mask!==maskRef || cell!==maskCell){
        maskRef=mask;maskCell=cell;maskTriangles=[];
        const m=identity();
        for(let r=0;r<mask.length;r++)for(let c=0;c<mask[r].length;c++)
          if(mask[r][c]===1)rect(maskTriangles,c*cell,r*cell,cell,cell,m);
      }
      stencil(maskTriangles,true);
    },
    end(){if(!recovery)flush();}
  };
};
