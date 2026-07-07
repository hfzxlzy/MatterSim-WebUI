# 调用 json 库格式化传入文件
import json
# 调用 pathlib 库解析文件路径
from pathlib import Path
# 导入 Three.js 引擎单文件位置
from webui.core.env import THREEJS_BUNDLE

# 结构模型显示html生成器
def Cell_renderer_html(
    rawdata,    # 结构数据
    phonondata,    # 声子数据
    mode="auto",    # auto/local/cdn
    threejs_url="https://cdn.jsdelivr.net/npm/three@v0.185.0/build/three.module.js",    # cdn_url
    addons_url="https://cdn.jsdelivr.net/npm/three@v0.185.0/examples/jsm/",    # cdn_url
):
    """
    返回一个 <iframe>，里面用 Three.js r184 (ESM) 渲染 ASE 结构。
    """
    # 格式化结构及声子元数据
    raw_js = json.dumps(rawdata)
    phonon_js = json.dumps(phonondata)
    # js结构信息块
    data_html = f"""
  <script>  
    const rawData = {raw_js};
    const phononData = {phonon_js};
    let classMode = "conventional"
    let data = rawData[classMode]
  </script>
"""
    # 3js调用信息头
    if mode == "local":
        threejs_bundle = Path(THREEJS_BUNDLE).read_text(encoding='utf-8')
        load_js = f"""
    <script type="module">
      // ============ 注入打包代码 ============
      const bundleCode = {json.dumps(threejs_bundle)};
      // ============ 创建 Blob URL ============
      const bundleURL = URL.createObjectURL(
        new Blob([bundleCode], {{ type: 'application/javascript' }})
      );
      console.log('✅ Blob URL 创建完成');
      // ============ 导入 ============
      // Rollup 打包的 ESM 会导出所有 export * 的内容
      const bundleExports = await import(bundleURL);
      console.log('✅ Three.js 加载成功');
      //console.log('导出内容:', Object.keys(THREE));
      // ============ 提取需要的模块 ============
      // Rollup 打包后，所有 export * 的内容都在 THREE 对象上
      ({{ OrbitControls, ConvexGeometry }} = bundleExports);
      // THREE 可能是 bundleExports 本身，也可能在 default 里
      THREE = bundleExports.default || bundleExports;

      console.log('THREE =', THREE);
      console.log('OrbitControls =', OrbitControls);
      console.log('ConvexGeometry =', ConvexGeometry);
"""
    elif mode == "cdn":
        load_js = f"""
    <script type="importmap">
    {{
      "imports":{{
        "three": "{threejs_url}",
        "three/addons/": "{addons_url}"
      }}
    }}
    </script>
    <script type="module">
      import * as THREE from 'three';
      import {{ OrbitControls }} from 'three/addons/controls/OrbitControls.js';
      import {{ ConvexGeometrys }} from 'three/addons/geometries/ConvexGeometry.js';

      console.log("THREE =", THREE);
      console.log("OrbitControls =", OrbitControls);
      console.log("ConvexGeometry =", ConvexGeometry);
"""
    else:
        # 读取本地 Three.js 源码 
        threejs_bundle = Path(THREEJS_BUNDLE).read_text(encoding='utf-8')
        load_js = f"""
    <script type="importmap">
      {{
        "imports":{{
          "three": "{threejs_url}",
          "three/addons/": "{addons_url}"
        }}
      }}
    </script>

    <script type="module">  
      console.log('🚀 尝试从 CDN 加载 Three.js...');
      let THREE, OrbitControls, ConvexGeometry;
      // ============ CDN 加载（带超时） ============
      const CDN_TIMEOUT = 1500; // 1.5秒超时
      try {{
        // 创建超时 Promise
        const timeoutPromise = new Promise((_, reject) => 
          setTimeout(() => reject(new Error('CDN 加载超时')), CDN_TIMEOUT)
        );
        // CDN 加载 Promise
        const cdnPromise = Promise.all([
          import("three"),
          import("three/addons/controls/OrbitControls.js"),
          import("three/addons/geometries/ConvexGeometry.js")
        ]);
        // 竞速：谁先完成用谁
        const results = await Promise.race([cdnPromise, timeoutPromise]);
        // 如果 CDN 成功
        const [threeModule, controlsModule, convexModule] = results;
        THREE = threeModule;
        OrbitControls = controlsModule.OrbitControls;
        ConvexGeometry = convexModule.ConvexGeometry;
        console.log("🌐 CDN Three.js 加载成功");
      }} catch (err) {{  
        console.log('❌ CDN 加载失败，从 Rollup 打包的单文件加载...');
        console.log('错误:', err.message);
        // ============ 注入打包代码 ============
        const bundleCode = {json.dumps(threejs_bundle)};
        // ============ 创建 Blob URL ============
        const bundleURL = URL.createObjectURL(
          new Blob([bundleCode], {{ type: 'application/javascript' }})
        );
        console.log('✅ Blob URL 创建完成');
        // ============ 导入 ============
        // Rollup 打包的 ESM 会导出所有 export * 的内容
        const bundleExports = await import(bundleURL);
        console.log('✅ Three.js 加载成功');
        //console.log('导出内容:', Object.keys(THREE));
        // ============ 提取需要的模块 ============
        // Rollup 打包后，所有 export * 的内容都在 THREE 对象上
        ({{ OrbitControls, ConvexGeometry }} = bundleExports);
        // THREE 可能是 bundleExports 本身，也可能在 default 里
        THREE = bundleExports.default || bundleExports;
      }}
        console.log('THREE =', THREE);
        console.log('OrbitControls =', OrbitControls);
        console.log('ConvexGeometry =', ConvexGeometry);
"""
    # 拼接完整html文件
    inner_html = f"""
{start(phonondata)}
<body>
<div id="main-container">
  {data_html}
  {hander(phonondata)}
  {js_renderer(load_js)}
  {js_ui(phonondata)}
</div>
</body>
</html>
"""
    return inner_html

# HTML文件头生成器
def start(phonondata):
    if phonondata is None:
        title = f"""结构预览"""
    else:
        title = f"""声子模式预览"""
    # html文件头及标签CSS
    html_start = f"""
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>
/* CSS 部分 */
  body {{
    margin: 0;
    font-family: "Microsoft YaHei", sans-serif;
    background: #f8f8f8;
  }}
  #main-container {{
    display: grid;
    grid-template-columns: 70% 30%;
    grid-template-rows: auto auto auto ;
    height: 100vh;
    border: 2px solid #000;
  }}
  #header {{
    grid-column: 1 / 4;
    display: grid;
    grid-template-columns: 40% 35% 25%; /* 左中右比例 */
    align-items: center;
    padding: 0.7em 1.2em;
    font-size: 1.25rem;
    font-weight: bold;
    border-bottom: 3px solid #000;
    background: #ffffff;
  }}
  #header-title {{
  font-size: 1.75rem;
  font-weight: bold;
  }}
  #header-cellparams, #header-formula {{
  font-size: 1rem;
  }}
  .header-label {{
    font-weight: bold;
    margin-bottom: 0.25em;
  }}
  .header-value {{
    font-weight: normal;
    font-size: 0.95rem;
  }}

  #viewer {{
    position: relative; /* 关键：让内部元素定位相对 viewer */
    display: flex;
    justify-content: flex-start; /* 靠左 */
    align-items: center;          /* 垂直居中 */
    width: 100%;
    height: 100%;
    border-right: 1px solid #aaa;
    background: #fff;
  }}

  #legend-box {{
    position: absolute;
    top: 2%;    /* 响应式位置 */
    right: 3%;    /* 响应式位置 */
    background: rgba(255,255,255,0.9);
    border: 1px solid #ccc;
    border-radius: 6px;
    padding: 1em 1.4em;    /* 随字体缩放 */
    font-size: 0.9rem;    /* DPI 自适应 */
    box-shadow: 0 2px 6px rgba(0,0,0,0.1);
    z-index: 1000; /* 确保在 Three.js 画布上方 */
  }}

  .legend-item {{
    display: flex;
    align-items: center;
    margin-bottom: 0.4em;    /* 随字体缩放 */
  }}

  .legend-color {{
    width: 0.9em;    /* 随字体缩放 */
    height: 0.9em;    /* 随字体缩放 */
    border-radius: 50%;
    margin-right: 6px;
    border: 1px solid #999;
  }}

  #controls {{
    padding: 0.6em;
    background: #f5f5f5;
    height: 70vh;        /* 控制面板最多占屏幕 72.4vh% 高度 */
    max-height: 70vh;
    overflow-y: auto;        /* 内容多时滚动，不挤压日志 */
  }}
  /* 单胞 / 常规晶胞按钮容器 */
  #cellmode-container {{
    display: grid;
    grid-template-columns: 1fr 1fr; /* 平分两列 */
    gap: 8px;
    margin-bottom: 12px;
  }}
  /* 单胞 / 常规晶胞按钮状态 */
  .cellmode-btn {{
    padding: 10px 0;
    border: 2px solid #333;
    border-radius: 6px;
    background: #e6e6e6;
    cursor: pointer;
    user-select: none;
    font-size: 16px;
    font-weight: bold;
    text-align: center;
    transition: background 0.15s, color 0.15s;
  }}
  .cellmode-btn:hover {{
    background: #dcdcdc;
  }}
  .cellmode-btn.active {{
    background: #666;     /* 选中变暗 */
    color: white;
    border-color: #222;
  }}
  /* 晶体学/配位化学 checkbox */
  #chemistry-mode {{
    display: grid;
    grid-template-columns: 1fr 1fr; /* 平分两列 */
    gap: 0.5em;
    margin-bottom: 1.0em;
  }}
  .chem-item {{
    font-size: 0.95rem;
    user-select: none;
  }}
  /* 禁用状态（单胞模式） */
  .chem-btn.disabled {{
    color: #aaa;
    cursor: not-allowed;
  }}
  /* 启用状态（常规晶胞模式） */
  .chem-btn.enabled {{
    color: #000;
    cursor: pointer;
  }}
  
  .section-box {{
    border: 2px solid #ccc;
    border-radius: 6px;
    padding: 0.8em 1em;
    margin-top: 1em;
    background: #fff;
  }}
  .section-title {{
    font-size: 1rem;
    font-weight: bold;
    margin-bottom: 0.5em;
    border-bottom: 1px solid #ddd;
    padding-bottom: 0.3em;
  }}

  /* 刻度条与滑块轨道保持完全一致的宽度 */
  .rotate-scale {{
    display: grid;
    grid-template-columns: 3.75em 1fr 1fr 1fr 1fr 1fr 3.75em; /* 五格布局 */
    font-size: 0.75rem;
    margin: 0.3em 0 0.8em 0;
    color: #555;
    white-space: nowrap;
  }}
  /* 默认：中间五格居中 */
  .rotate-scale span {{
    justify-self: center;
    text-align: center;
  }}
  /* 左二格子左对齐 */
  .rotate-scale span:nth-child(2) {{
    justify-self: start;
    text-align: left;
  }}
  /* 右二格子右对齐 */
  .rotate-scale span:nth-child(6) {{
    justify-self: end;
    text-align: right;
  }}
  .rotate-row {{
    display: grid;
    grid-template-columns: 4em 1fr 4em;
    align-items: center;
    margin-bottom: 0.5em;
    font-size: 0.95rem;
  }}
  .rotate-row span {{
    text-align: right;
    font-weight: bold;
    color: #333;
  }}
  /* 通用：去掉默认样式 */
  input[type="range"] {{
    -webkit-appearance: none;
    width: 100%;
    height: 0.4em;
    border-radius: 0.2em;
    background: transparent; /* 轨道颜色我们单独设置 */
  }}
  #rotateA {{ background: linear-gradient(to right, #ff4d4d, #ddd); }}
  #rotateB {{ background: linear-gradient(to right, #4dff4d, #ddd); }}
  #rotateC {{ background: linear-gradient(to right, #4d4dff, #ddd); }}

  #result-area {{
    grid-column: 1 / 3;
    padding: 0.6em 1em;
    border-top: 1px solid #aaa;
    background: #fafafa;
    height: 12.5vh;    /* 占屏幕高度 12.5% */
    max-height: 12.5vh;    /* 占屏幕高度 27.5% */
    overflow-y: auto;
    text-align: left;
    font-size: 0.9rem;
    color: #333;
  }}
  #log-content {{
    font-family: Consolas, monospace;
    font-size: 0.9rem;
    line-height: 1.5;
    color: #444;
  }}
  #log-watermark {{
    text-align: center;
    font-family: "Microsoft YaHei", "Heiti SC", "Noto Sans CJK", sans-serif;    /* 粗黑体 */
    font-weight: 900;        
    font-size: 2.5rem;         /* 大字号 */
    color: #72727255;             /* 淡灰色 */
    padding: 0.5em 0;
    user-select: none;       /* 不可选中 */
  }}
  .log-entry {{
    padding: 0.3em 0;
    font-size: 1.0rem;
    color: #333;
  }}
  .distance,
  .angle,
  .dihedral{{
    font-family: Consolas, monospace;
    font-size: 0.9rem;
    line-height: 1.5;
  }}
  .distance {{ color: #063714; }}
  .angle    {{ color: #5c0707; }}
  .dihedral {{ color: #07195c; }}

  .phonon-bar {{
    display: flex;
    align-items: center;
    gap: 0.6em;
    margin-top: 0.6em;
    font-size: 0.9rem;
  }}

  .expand-bar input {{
    width: 3.2em;
    height: 1.75em;
    padding: 0.2em 0.3em;
    font-size: 0.9rem;
    box-sizing: border-box;
  }}

  /* 输入框统一大小 */
  .phonon-bar input {{
    width: 4em;
    height: 1.75em;
    padding: 0.2em 0.5em;
    font-size: 0.9rem;
    box-sizing: border-box;
  }}
  /* 按钮统一大小 */
  .phonon-btn {{
    width: 5em;
    height: 1.75em;
    font-size: 0.9rem;
    cursor: pointer;
    border: 1px solid #888;
    background: #f0f0f0;
    border-radius: 4px;
    transition: 0.15s;
  }}
  .phonon-btn:hover {{
    background: #e0e0e0;
  }}
  .phonon-btn.active {{
    background: #666;     /* 选中变暗 */
    color: white;
    border-color: #222;
  }}
</style>
</head>
"""
    
    return html_start

# 结构信息显示块生成器
def hander(phonondata):
    # 当未传入声子数据时不载入声子信息显示相关UI
    if phonondata is None:
      title = f"""
    <div id="header-title">结构预览</div>
"""
      phonon_script = f""""""
    # 否则载入声子信息显示相关UI
    else:
      title = f"""
    <div id="header-title">声子模式预览
      <div class="header-value">
        Q点 : (<span id="q_position">--</span>)&nbsp;&nbsp;
        频率 : <span id="frequency">--</span>&nbsp;THz
      </div>
    </div>
"""
      phonon_script =f"""
      // Q-point
      document.getElementById("q_position").textContent = 
        phononData.q_position.map(v => v.toFixed(2)).join(", ");
      // 模式频率
      document.getElementById("frequency").textContent = 
        phononData.band[0].frequency.toExponential(3);
"""
    # 主信息展示UI
    html_hander = f"""
  <div id="header">
    {title}

    <div id="header-cellparams">
      <div class="header-label">晶胞参数</div>
      <div class="header-value">
        a = <span id="param-a">--</span> Å，
        b = <span id="param-b">--</span> Å，
        c = <span id="param-c">--</span> Å<br>
        α = <span id="param-alpha">--</span>°，
        β = <span id="param-beta">--</span>°，
        γ = <span id="param-gamma">--</span>°
      </div>
    </div>

    <div id="header-formula">
      <div class="header-label">化学式</div>
      <div class="header-value" id="chem-formula">--</div>
    </div>
    <script>
       function updataHeader(data){{
        // === 1. 读取 cell ===
        const cell = data.cell;
        const a = cell[0];    //a
        const b = cell[1];    //b
        const c = cell[2];    //c
        // === 2. 向量长度 ===
        function vecLength(v) {{
          return Math.sqrt(v[0]**2 + v[1]**2 + v[2]**2);
        }}
        // === 3. 向量点积 ===
        function dot(a, b) {{
          return a[0]*b[0] + a[1]*b[1] + a[2]*b[2];
        }}
        // === 4. 向量夹角（返回角度） ===
        function angleBetween(a, b) {{
          const cos = dot(a,b) / (vecLength(a) * vecLength(b));
          return Math.acos(cos) * 180 / Math.PI;
        }}
        // === 5. 计算晶胞参数 ===
        const lenA = vecLength(a);    //a
        const lenB = vecLength(b);    //b
        const lenC = vecLength(c);    //c
        const alpha = angleBetween(b, c);    // α = ∠(b,c)
        const beta  = angleBetween(a, c);    // β = ∠(a,c)
        const gamma = angleBetween(a, b);    // γ = ∠(a,b)
        // === 6. 写入 HTML ===
        document.getElementById("param-a").textContent = lenA.toFixed(3);    //a
        document.getElementById("param-b").textContent = lenB.toFixed(3);    //b
        document.getElementById("param-c").textContent = lenC.toFixed(3);    //c
        document.getElementById("param-alpha").textContent = alpha.toFixed(2);   // α
        document.getElementById("param-beta").textContent  = beta.toFixed(2);    // β
        document.getElementById("param-gamma").textContent = gamma.toFixed(2);   // γ
      }}
      // 化学式
      document.getElementById("chem-formula").textContent = rawData.primitive.formula;
      {phonon_script}
    </script>
  </div>
"""
    
    return html_hander

# 结构模型渲染及交互块生成器
def js_renderer(load_js):
    js_renderer = f"""
  <div id="viewer">
    {load_js}
      // ===============================
      // 0. data预处理
      // ===============================
      function concat(a, b) {{
        // 如果是 TypedArray（Float32Array / Uint32Array / Int16Array 等）
        if (ArrayBuffer.isView(a) && ArrayBuffer.isView(b)) {{
          const out = new a.constructor(a.length + b.length);
          out.set(a, 0);
          out.set(b, a.length);
          return out;
        }}
        // 否则当普通 Array 处理
        return a.concat(b);
      }}
      function near(v, eps = 5e-2) {{
          return (v > -eps && v < eps) || (v > 1 - eps && v < 1 + eps);
      }}
      // buildAdjacencyList()——识别多面体中心构建邻接表
      function buildAdjacencyList(data) {{
        const N = data.natoms;
        const adj = Array.from({{ length: N }}, () => []);
        // 成键信息矩阵化
        for (const b of data.bonds.filter(b => data.charges[b.i] >= 0)) {{
          adj[b.i].push({{ j: b.j, offset: b.offset }});
          adj[b.j].push({{ j: b.i, offset: [-b.offset[0], -b.offset[1], -b.offset[2]] }});
        }}
        return adj;
      }};
      // classifyShared()——判断晶胞中原子共用成分
      function classifyShared(fr, index, eps = 5e-2) {{
        const fx = fr[0], fy = fr[1], fz = fr[2];
        const nearX = near(fx, eps);
        const nearY = near(fy, eps);
        const nearZ = near(fz, eps);
        let count = 0;
        if (nearX) count++;
        if (nearY) count++;
        if (nearZ) count++;
        let type = "inside"
        if (nearX && nearY && nearZ) {{
          type = "corner";  // 顶点
        }} else if (nearY && nearZ) {{
          type = "edgeX";   // 棱方向 ∥ X
        }} else if (nearX && nearZ) {{
          type = "edgeY";   // 棱方向 ∥ Y
        }} else if (nearX && nearY) {{
          type = "edgeZ";   // 棱方向 ∥ Z
        }} else if (nearX) {{
          type = "faceX";   // 面方向 ⟂ X
        }} else if (nearY) {{
          type = "faceY";   // 面方向 ⟂ Y
        }} else if (nearZ) {{
          type = "faceZ";   // 面方向 ⟂ Z
        }}
        //if (count != 0) {{
        //  console.log(
        //    `shared atom index=${{index}}, type=${{type}}, frac=(${{fx}}, ${{fy}}, ${{fz}})`
        //  );
        //}}
        return {{ count, type, nearX, nearY, nearZ ,fr}};
      }}
      // buildShifts()——根据共用原子信息确定平移操作方式
      function buildShifts(info) {{
        const shifts = [];
        const sx = (info.fr[0] < 0.5 ? +1 : -1);
        const sy = (info.fr[1] < 0.5 ? +1 : -1);
        const sz = (info.fr[2] < 0.5 ? +1 : -1);
        // 面
        if (info.count === 1) {{
          if (info.nearX) shifts.push([sx,0,0]);
          if (info.nearY) shifts.push([0,sy,0]);
          if (info.nearZ) shifts.push([0,0,sz]);
          return shifts;
        }}
        // 棱
        if (info.count === 2) {{
          if (info.nearX && info.nearY) {{
            shifts.push([sx,0,0], [0,sy,0], [sx,sy,0]);
          }}
          if (info.nearX && info.nearZ) {{
            shifts.push([sx,0,0], [0,0,sz], [sx,0,sz]);
          }}
          if (info.nearY && info.nearZ) {{
            shifts.push([0,sy,0], [0,0,sz], [0,sy,sz]);
          }}
          return shifts;
        }}
        // 顶点
        if (info.count === 3) {{
          shifts.push([sx,0,0]);
          shifts.push([0,sy,0]);
          shifts.push([0,0,sz]);
          shifts.push([sx,sy,0]);
          shifts.push([sx,0,sz]);
          shifts.push([0,sy,sz]);
          shifts.push([sx,sy,sz]);
          return shifts;
        }}
        return shifts;
      }}
      // buildShellCell()——构建“壳单胞”
      function buildShellCell(data, mod) {{
        // 获取显示模式
        const {{ chemistryMode }} = mod;
        // 获取原始数据
        const A = data.cell;
        const N = data.natoms;
        // 定义壳单胞参数
        const shellPositions = [];    // 笛卡尔坐标
        const shellF2        = [];    // 分数坐标
        const shellSymbols   = [];    // 元素种类
        const shellRadii     = [];    // 原子半径
        const shellColors    = [];    // 原子颜色
        const shellCharges   = [];    // 原子电性
        const shellBonds     = [];    // 成键信息
        // key: `${{i}}_${{ox}}_${{oy}}_${{oz}}` → newIndex
        const map = new Map();  
        // 原胞原子的扩胞模式
        const baseType = new Array(N).fill(null);
        // 壳原子类型（face / edge / corner）
        const shellType = [];
        // 原胞原子 index（用于过滤 offset=0）
        const originalMap = new Set();
        for (let i = 0; i < N; i++) {{
          originalMap.add(i);
        }}
        // 复制函数（统一过滤 offset=0）
        function copyAtom(i, ox, oy, oz, allowOriginal = false) {{
          const isOriginal = (ox === 0 && oy === 0 && oz === 0);
          // 原胞本体 offset=0 不复制（除非 allowOriginal=true）
          if (!allowOriginal && ox === 0 && oy === 0 && oz === 0 && originalMap.has(i)) {{
            return null;
          }}
          const key = `${{i}}_${{ox}}_${{oy}}_${{oz}}`;
          if (map.has(key)) return map.get(key);
          const fr = data.scaled_positions[i];
          let cart;
          if (isOriginal) {{
            // 本体：不要加 offset
            cart = [
              fr[0] * A[0][0] + fr[1] * A[1][0] + fr[2] * A[2][0],
              fr[0] * A[0][1] + fr[1] * A[1][1] + fr[2] * A[2][1],
              fr[0] * A[0][2] + fr[1] * A[1][2] + fr[2] * A[2][2]
            ];
          }} else {{
            // 镜像：加 offset
            cart = [
              (fr[0] + ox) * A[0][0] + (fr[1] + oy) * A[1][0] + (fr[2] + oz) * A[2][0],
              (fr[0] + ox) * A[0][1] + (fr[1] + oy) * A[1][1] + (fr[2] + oz) * A[2][1],
              (fr[0] + ox) * A[0][2] + (fr[1] + oy) * A[1][2] + (fr[2] + oz) * A[2][2]
            ];
          }}
          const newIndex = shellPositions.length;
          shellPositions.push(cart);
          shellSymbols.push(data.symbols[i]);
          shellRadii.push(data.radii[i]);
          shellColors.push(data.colors[i]);
          shellCharges.push(data.charges[i]);
          // 壳胞分数坐标 = 原胞分数坐标 + 偏移
          let f2x = fr[0] + ox;
          let f2y = fr[1] + oy;
          let f2z = fr[2] + oz;
          shellF2[newIndex] = [f2x, f2y, f2z];
          shellType[newIndex] = baseType[i];    // 镜像继承类型
          map.set(key, newIndex);
          return newIndex;
        }}
        // 邻接表（含 offset）
        const adj = buildAdjacencyList(data);
        const tasks = [];
        // 第一步：生成所有复制任务并分类 face/edge/corner
        for (let i = 0; i < N; i++) {{
          const fr = data.scaled_positions[i];
          const info = classifyShared(fr, i);
          if (info.count === 0) continue;
          // 记录壳原子类型（镜像自动继承）
          baseType[i] = info.type;
          // 本体（offset=0）
          tasks.push({{ i, ox:0, oy:0, oz:0, allowOriginal:false }});

          // 使用完整平移生成器
          const shifts = buildShifts(info);
          for (const [ox,oy,oz] of shifts) {{
            tasks.push({{ i, ox, oy, oz, allowOriginal:false }});
          }}
          // 阳离子 → 补齐邻居（保持你原来的逻辑）
          if (data.charges[i] > 0) {{
            const i_shifts = [[0,0,0], ...shifts];
            for (const [iox, ioy, ioz] of i_shifts) {{
              for (const nb of adj[i]) {{
                const j = nb.j;
                baseType[j] = baseType[i];
                const ox = iox + nb.offset[0];
                const oy = ioy + nb.offset[1];
                const oz = ioz + nb.offset[2];
                tasks.push({{ i:j, ox, oy, oz, allowOriginal:true }});
              }}
            }}
          }}
        }}
        // 第二步：统一执行任务（过滤在 copyAtom 内部做）
        for (const t of tasks) {{
          copyAtom(t.i, t.ox, t.oy, t.oz, t.allowOriginal);
        }}
        // 第三步：建立键（只在阳离子镜像之间建立）
        for (let i = 0; i < N; i++) {{
          if (data.charges[i] <= 0) continue;
          const fr = data.scaled_positions[i];
          const info = classifyShared(fr, i);
          if (info.count === 0) continue;
          // 本体 + 镜像方向，必须和上面生成邻居任务时保持一致
          // 使用与第一步完全一致的平移方向
          const i_shifts = [[0,0,0], ...buildShifts(info)];
          for (const [iox, ioy, ioz] of i_shifts) {{
            const i_new = map.get(`${{i}}_${{iox}}_${{ioy}}_${{ioz}}`);
            if (i_new == null) continue;
            for (const nb of adj[i]) {{
              const j = nb.j;
              // 邻居 offset = 本体 offset + 邻居相对 offset
              const jox = iox + nb.offset[0];
              const joy = ioy + nb.offset[1];
              const joz = ioz + nb.offset[2];
              const j_new = map.get(`${{j}}_${{jox}}_${{joy}}_${{joz}}`);
              if (j_new == null) continue; 
              shellBonds.push({{ i: i_new, j: j_new, offset:[0,0,0] }});
              shellBonds.push({{ i: j_new, j: i_new, offset:[0,0,0] }});
            }}
          }}
        }}
        //console.log("=== shellData(", chemistryMode, ") ===");
        //console.log("positions:", shellPositions);
        //console.log("scaled_positions:", shellF2);
        //console.log("symbols:", shellSymbols);
        //console.log("radii:", shellRadii);
        //console.log("colors:", shellColors);
        //console.log("charges:", shellCharges);
        //console.log("bonds:", shellBonds);
        //console.log("natoms:", shellPositions.length);
        //console.log("type", shellType);
        return {{
          positions: shellPositions,

          symbols:   shellSymbols,
          scaled_positions:    shellF2,
          radii:     shellRadii,
          colors:    shellColors,
          charges:   shellCharges,
          bonds:     shellBonds,
          cell:      data.cell,
          pbc:       data.pbc,
          natoms:    shellPositions.length,
          shellType
        }};
      }}

      // ===============================
      // 1. supercell 数据层（纯数学）
      // ===============================
      // buildSupercore()——超胞数据生成(晶胞核)
      function buildSupercore(data, nx, ny, nz) {{
        const N = data.positions.length;
        const M = nx * ny * nz;
        // 原胞坐标矩阵 P (N×3)
        const P = new Float32Array(N * 3);
        for (let i = 0; i < N; i++) {{
            const p = data.positions[i];
            P[i*3]   = p[0];
            P[i*3+1] = p[1];
            P[i*3+2] = p[2];
        }}
        // 晶胞矩阵 A (3×3)
        const A = data.cell;
        // 生成偏移矩阵 S (M×3)
        const S = new Float32Array(M * 3);
        const cellXYZ = new Array(M);
        let idx = 0;
        let c = 0;
          for (let ix = 0; ix < nx; ix++) {{
            for (let iy = 0; iy < ny; iy++) {{
              for (let iz = 0; iz < nz; iz++) {{
                S[idx]   = ix;
                S[idx+1] = iy;
                S[idx+2] = iz;
                idx += 3;
                cellXYZ[c++] = [ix, iy, iz];
              }}
            }}
          }}
        // baseIndex / cellIndex
        const total = N * M;
        const baseIndex = new Uint16Array(total);
        const cellIndex = new Uint16Array(total);
        let inst = 0;
        for (let s = 0; s < M; s++) {{
          for (let i = 0; i < N; i++) {{
            baseIndex[inst] = i;
            cellIndex[inst] = s;
            inst++;
          }}
        }}
        // 预计算 cellOffset[M × 3]
        const cellOffset = new Float32Array(M * 3);
        for (let s = 0; s < M; s++) {{
          const ix = S[s*3];
          const iy = S[s*3+1];
          const iz = S[s*3+2];

          cellOffset[s*3]   = ix*A[0][0] + iy*A[1][0] + iz*A[2][0];
          cellOffset[s*3+1] = ix*A[0][1] + iy*A[1][1] + iz*A[2][1];
          cellOffset[s*3+2] = ix*A[0][2] + iy*A[1][2] + iz*A[2][2];
        }}
        // 预计算 atomWorldPos[N*M × 3]
        const atomWorldPos = new Float32Array(total * 3);
        for (let inst = 0; inst < total; inst++) {{
          const base = baseIndex[inst];
          const cell = cellIndex[inst];

          atomWorldPos[inst*3]   = P[base*3]   + cellOffset[cell*3];
          atomWorldPos[inst*3+1] = P[base*3+1] + cellOffset[cell*3+1];
          atomWorldPos[inst*3+2] = P[base*3+2] + cellOffset[cell*3+2];
        }}
        // 超胞晶胞矩阵
        const superCell = [
          [A[0][0] * nx, A[0][1] * nx, A[0][2] * nx],
          [A[1][0] * ny, A[1][1] * ny, A[1][2] * ny],
          [A[2][0] * nz, A[2][1] * nz, A[2][2] * nz]
        ];
        //console.log("=== ori ===");
        //console.log("ori.baseIndex.length =", baseIndex.length);
        //console.log("ori.cellIndex.length =", cellIndex.length);
        //console.log("ori.cellXYZ.length   =", cellXYZ.length);
        //console.log("ori.S.length         =", S.length);
        return {{
          P,          // 单胞笛卡尔坐标
          A,          // 晶格矩阵
          S,          // 偏移矩阵
          cellXYZ,    // cell 的 (ix,iy,iz)
          baseIndex,  // 实例对应单胞原子
          cellIndex,  // 实例对应 cell
          cellOffset,      // 超胞单元偏移
          atomWorldPos,    // 超胞原子空间坐标
          superCell,    // 超胞胞矩阵
          N,     // 原胞原子数
          M,    // 单胞数量
          nx, ny, nz,    //扩胞系数
        }};
      }}
      //buildSupershell()——超胞数据生成(晶胞壳)
      function buildSupershell(shellData, nx, ny, nz){{
        // 去重地图：key = `${{i}}_${{ox}}_${{oy}}_${{oz}}`
        const seen = new Map();        
        const A = shellData.cell;
        const N = shellData.natoms;
        // 1. P（壳单胞原子坐标）
        const P = new Float32Array(N * 3);
        for (let i = 0; i < N; i++) {{
          const p = shellData.positions[i];
          P[i*3]   = p[0];
          P[i*3+1] = p[1];
          P[i*3+2] = p[2];
        }}
        const FR = shellData.scaled_positions;   // 原胞分数坐标
        const T  = shellData.shellType;     // faceX / edgeY / corner …
        // 先用普通数组收集实例
        const baseIndexArr  = [];
        const cellXYZArr    = [];
        const atomWorldArr  = [];
        const cellOffsetArr = [];
        // 等步递推尾迹函数
        function range(start, end) {{
          const arr = [];
          // 从系数起点构建等差递推数列
          for (let i = start; i <= end; i++) arr.push(i);
          return arr;
        }}
        // 偏移函数
        function addInstance(i, ox, oy, oz){{
          const key = `${{i}}_${{ox}}_${{oy}}_${{oz}}`;
          // 如果已经生成过 → 跳过
          if (seen.has(key)) return;
          seen.set(key, true);
          const px = P[i*3];
          const py = P[i*3+1];
          const pz = P[i*3+2];

          const dx = ox*A[0][0] + oy*A[1][0] + oz*A[2][0];
          const dy = ox*A[0][1] + oy*A[1][1] + oz*A[2][1];
          const dz = ox*A[0][2] + oy*A[1][2] + oz*A[2][2];

          baseIndexArr.push(i);
          cellXYZArr.push([ox, oy, oz]);
          cellOffsetArr.push(dx, dy, dz);
          atomWorldArr.push(px + dx, py + dy, pz + dz);
        }}
        // 主循环：按 type + fr 生成偏移
        for (let i = 0; i < N; i++) {{
          const type = T[i];
          const fr   = FR[i];
          if (!fr || !type) continue;

          const fx = fr[0];
          const fy = fr[1];
          const fz = fr[2];
          // faceX
          if (type === "faceX") {{
            for (let oy = 0; oy < ny; oy++) {{
              for (let oz = 0; oz < nz; oz++) {{
                if (fx < 0.5) {{for (let ox = 0; ox < nx - 1; ox++) {{addInstance(i, ox, oy, oz);}}}}     // 尾迹
                addInstance(i, nx - 1, oy, oz);              // 终点
              }}
            }}
          }}
          // faceY
          else if (type === "faceY") {{
            for (let ox = 0; ox < nx; ox++) {{
              for (let oz = 0; oz < nz; oz++) {{
                if (fy < 0.5) {{for (let oy = 0; oy < ny - 1; oy++) {{addInstance(i, ox, oy, oz);}}}};
                addInstance(i, ox, ny - 1, oz);
              }}
            }}
          }}
          // faceZ
          else if (type === "faceZ") {{
            for (let ox = 0; ox < nx; ox++) {{
              for (let oy = 0; oy < ny; oy++) {{
                if (fz < 0.5) {{for (let oz = 0; oz < nz - 1; oz++) {{addInstance(i, ox, oy, oz);}}}};
                addInstance(i, ox, oy, nz - 1);
              }}
            }}
          }}
          // edgeX（沿 X 的棱 → Y/Z 两方向 trace）
          else if (type === "edgeX") {{
            const yList = fy < 0.5 ? range(0, ny-1) : [ny-1];
            const zList = fz < 0.5 ? range(0, nz-1) : [nz-1];

            for (let ox = 0; ox < nx; ox++) {{
              for (const oy of yList) {{
                for (const oz of zList) {{
                  addInstance(i, ox, oy, oz);
                }}
              }}
            }}
          }}
          // edgeY（沿 Y 的棱 → X/Z 两方向 trace）
          else if (type === "edgeY") {{
            const xList = fx < 0.5 ? range(0, nx-1) : [nx-1];
            const zList = fz < 0.5 ? range(0, nz-1) : [nz-1];

            for (let oy = 0; oy < ny; oy++) {{
              for (const ox of xList) {{
                for (const oz of zList) {{
                  addInstance(i, ox, oy, oz);
                }}
              }}
            }}
          }}
          // edgeZ（沿 Z 的棱 → X/Y 两方向 trace）
          else if (type === "edgeZ") {{
            const xList = fx < 0.5 ? range(0, nx-1) : [nx-1];
            const yList = fy < 0.5 ? range(0, ny-1) : [ny-1];

            for (let oz = 0; oz < nz; oz++) {{
              for (const ox of xList) {{
                for (const oy of yList) {{
                  addInstance(i, ox, oy, oz);
                }}
              }}
            }}
          }}
          // corner（三方向 trace）
          else if (type === "corner") {{
            const xList = fx < 0.5 ? range(0, nx-1) : [nx-1];
            const yList = fy < 0.5 ? range(0, ny-1) : [ny-1];
            const zList = fz < 0.5 ? range(0, nz-1) : [nz-1];

            for (const ox of xList)
              for (const oy of yList)
                for (const oz of zList)
                  addInstance(i, ox, oy, oz);
          }}
          // interior：只放在原胞
          else {{
            addInstance(i, 0, 0, 0);
          }}
        }}
        // 4. 分配 TypedArray
        const M = baseIndexArr.length;
        const baseIndex = new Uint32Array(M);    // 实例对应壳单胞原子
        const cellIndex = new Uint32Array(M);    // 实例对应 cell (ox,oy,oz)
        const atomWorldPos = new Float32Array(M * 3);    // 扩胞后坐标
        const S = new Float32Array(M * 3);     // 偏移矩阵 (M×3)
        const cellXYZ = new Array(M);    // (ix,iy,iz)
        const cellOffset = new Float32Array(M * 3);    // 偏移后的笛卡尔坐标
        // 5. 主循环（复制 + 二分 + 推移）
        for (let inst = 0; inst < M; inst++) {{
          baseIndex[inst] = baseIndexArr[inst];
          cellIndex[inst] = inst;

          const [ox, oy, oz] = cellXYZArr[inst];
          cellXYZ[inst] = [ox, oy, oz];
          S[inst*3]   = ox;
          S[inst*3+1] = oy;
          S[inst*3+2] = oz;

          cellOffset[inst*3]   = cellOffsetArr[inst*3];
          cellOffset[inst*3+1] = cellOffsetArr[inst*3+1];
          cellOffset[inst*3+2] = cellOffsetArr[inst*3+2];

          atomWorldPos[inst*3]   = atomWorldArr[inst*3];
          atomWorldPos[inst*3+1] = atomWorldArr[inst*3+1];
          atomWorldPos[inst*3+2] = atomWorldArr[inst*3+2];
        }}
        // 6. 超胞矩阵
        const superCell = [
          [A[0][0] * nx, A[0][1] * nx, A[0][2] * nx],
          [A[1][0] * ny, A[1][1] * ny, A[1][2] * ny],
          [A[2][0] * nz, A[2][1] * nz, A[2][2] * nz]
        ];
        //console.log(cellXYZ);
        return {{
          P,          // 壳胞笛卡尔坐标
          A,          // 晶格矩阵
          S,          // 偏移矩阵
          cellXYZ,    // cell 的 (ix,iy,iz)
          baseIndex,  // 实例对应壳胞原子
          cellIndex,  // 实例对应 cell
          cellOffset,      // 超胞壳单元偏移
          atomWorldPos,    // 超胞壳原子空间坐标
          superCell,    // 超胞壳矩阵
          N,     // 壳胞原子数
          M,    // 壳胞数量
          nx, ny, nz,    //扩胞系数
        }};
      }};
      // mergeSupercells()——超胞数据生成(调度)
      function mergeSupercells(data, mod, nx, ny, nz) {{
        const {{ cellMode, chemistryMode }} = mod;
        //MODE 1: primitive —— 只显示原胞 + 只显示 offset=[0,0,0] 的键
        if (cellMode === "primitive") {{
          const primitiveData = {{
            positions: data.positions,
            scaled_positions: data.scaled_positions,
            symbols:   data.symbols,
            radii:     data.radii,
            colors:    data.colors,
            charges:   data.charges,
            bonds:     data.bonds,
            cell:      data.cell,
            pbc:       data.pbc,
            natoms:    data.natoms
          }};

          const core = buildSupercore(data, nx, ny, nz);

        // === cellXYZ 必须是按 cell 存的（长度 M）===
          const newCellXYZ = core.cellXYZ;   // 直接引用，不要展开成实例级
          // === 实例级数据 ===
          const newBaseIndex  = Array.from(core.baseIndex);
          const newCellIndex  = Array.from(core.cellIndex);
          const newCellOffset = Array.from(core.cellOffset);
          const newS          = Array.from(core.S);
          // === 扩胞 bonds（用正确的 S_A / S_B）===
          const expandedBonds = [];
          const totalInst = newBaseIndex.length;

          for (let instA = 0; instA < totalInst; instA++) {{

            const atomA = newBaseIndex[instA];
            const cellA = newCellIndex[instA];

            const S_A = [
              core.S[cellA * 3],
              core.S[cellA * 3 + 1],
              core.S[cellA * 3 + 2],
            ];

            for (const b of data.bonds) {{
              if (b.i !== atomA) continue;

              const atomB = b.j;

              const S_B = [
                S_A[0] + b.offset[0],
                S_A[1] + b.offset[1],
                S_A[2] + b.offset[2],
              ];

              let instB = -1;
              for (let inst = 0; inst < totalInst; inst++) {{
                if (newBaseIndex[inst] !== atomB) continue;

                const cellB = newCellIndex[inst];
                if (core.S[cellB * 3]     === S_B[0] &&
                    core.S[cellB * 3 + 1] === S_B[1] &&
                    core.S[cellB * 3 + 2] === S_B[2]) {{
                  instB = inst;
                  break;
                }}
              }}

              if (instB !== -1) {{
                expandedBonds.push({{ instA, instB, offset: b.offset }});
              }}
            }}
          }}

          return {{
            P: new Float32Array(primitiveData.positions.flat()),
            atomWorldPos: new Float32Array(core.atomWorldPos),

            baseIndex: new Uint32Array(newBaseIndex),
            cellIndex: new Uint32Array(newCellIndex),
            A: core.A,
            S: core.S,
            cellXYZ: newCellXYZ,   
            cellOffset: new Float32Array(core.cellOffset),
            superCell: core.superCell,

            N: data.natoms,
            M: totalInst,

            nx: core.nx,
            ny: core.ny,
            nz: core.nz,

            bonds: expandedBonds,
            call: "instanceBonds",

            data: primitiveData
          }};
        }} else {{
          // MODE 2: chemistryMode = coordination —— 原胞 + 共用原子
          if(chemistryMode === "coordination"){{
            // 构建壳单胞
            const shellData  = buildShellCell(data, mod);
            const core       = buildSupercore(data, nx, ny, nz);
            const shell      = buildSupershell(shellData, nx, ny, nz);
            // 修正壳胞 baseIndex 偏移
            for (let i = 0; i < shell.baseIndex.length; i++) {{
              shell.baseIndex[i] += data.natoms;
            }}
            // 修正壳胞 bond 偏移
            const shiftedShellBonds = shellData.bonds.map(b => ({{
              i: b.i + data.natoms,
              j: b.j + data.natoms,
              offset: b.offset
            }}));
            // 合并 data（用于渲染）
            const coordinationData = {{
              positions: data.positions.concat(shellData.positions),
              scaled_positions: data.scaled_positions.concat(shellData.scaled_positions),
              symbols:   data.symbols.concat(shellData.symbols),
              radii:     data.radii.concat(shellData.radii),
              colors:    data.colors.concat(shellData.colors),
              charges:   data.charges.concat(shellData.charges),
              bonds:     data.bonds.concat(shiftedShellBonds),
              cell:      data.cell,
              pbc:       data.pbc,
              natoms:    data.natoms + shellData.natoms
            }};
            // 统一合并 core + shell 实例）
            const totalInstances = core.baseIndex.length + shell.baseIndex.length;
            // baseIndex
            const mergedBaseIndex = concat(core.baseIndex, shell.baseIndex);
            // cellIndex
            const mergedCellIndex = concat(core.cellIndex, shell.cellIndex);
            // atomWorldPos
            const mergedAtomWorldPos = concat(core.atomWorldPos, shell.atomWorldPos);
            // S（按实例展开）
            const mergedS = new Float32Array(totalInstances * 3);
            for (let i = 0; i < core.baseIndex.length; i++) {{
              const s = core.cellIndex[i];
              mergedS[i*3]   = core.S[s*3];
              mergedS[i*3+1] = core.S[s*3+1];
              mergedS[i*3+2] = core.S[s*3+2];
            }}
            for (let i = 0; i < shell.baseIndex.length; i++) {{
              const j = core.baseIndex.length + i;
              const s = shell.cellIndex[i];
              mergedS[j*3]   = shell.S[s*3];
              mergedS[j*3+1] = shell.S[s*3+1];
              mergedS[j*3+2] = shell.S[s*3+2];
            }}
            // cellXYZ（按实例展开）
            const mergedCellXYZ = [];
            for (let i = 0; i < core.baseIndex.length; i++) {{
              mergedCellXYZ.push(core.cellXYZ[core.cellIndex[i]]);
            }}
            for (let i = 0; i < shell.baseIndex.length; i++) {{
              mergedCellXYZ.push(shell.cellXYZ[shell.cellIndex[i]]);
            }}
            // cellOffset
            const mergedCellOffset = concat(core.cellOffset, shell.cellOffset);
            // 返回统一结构
            return {{
              P:            concat(core.P, shell.P),
              atomWorldPos: mergedAtomWorldPos,
              baseIndex:    mergedBaseIndex,
              cellIndex:    mergedCellIndex,

              A: core.A,
              S: mergedS,
              cellXYZ: mergedCellXYZ,
              cellOffset: mergedCellOffset,
              superCell: core.superCell,

              N: coordinationData.natoms,
              M: totalInstances,
              nx: core.nx,
              ny: core.ny,
              nz: core.nz,

              call: "analyticalBonds",

              data: coordinationData
            }};
          // MODE 3: chemistryMode = crystal —— 原胞 + 共用原子（不扩胞）
          }} else {{
            if (chemistryMode === "crystal"){{
              function insideCell(fr, eps=5e-2, nx=1, ny=1, nz=1 ) {{
                return (
                  fr[0] >= -eps && fr[0] <= nx+eps &&
                  fr[1] >= -eps && fr[1] <= ny+eps &&
                  fr[2] >= -eps && fr[2] <= nz+eps
                );
              }}
              // --- 1. 构建壳单胞 ---
              const shellData  = buildShellCell(data, mod);
              const core       = buildSupercore(data, nx, ny, nz);
              const shell      = buildSupershell(shellData, nx, ny, nz);
              // 修正壳胞 baseIndex 偏移
              for (let i = 0; i < shell.baseIndex.length; i++) {{
                shell.baseIndex[i] += data.natoms;
              }}
              // 修正壳胞 bond 偏移
              const shiftedShellBonds = shellData.bonds.map(b => ({{
                i: b.i + data.natoms,
                j: b.j + data.natoms,
                offset: b.offset
              }}));
              // --- 2. 合胞数据（原胞 + 壳胞） ---
              const crystalData = {{
                positions: data.positions.concat(shellData.positions),
                scaled_positions: data.scaled_positions.concat(shellData.scaled_positions),
                symbols:   data.symbols.concat(shellData.symbols),
                radii:     data.radii.concat(shellData.radii),
                colors:    data.colors.concat(shellData.colors),
                charges:   data.charges.concat(shellData.charges),
                bonds:     data.bonds.concat(shiftedShellBonds),
                cell:      data.cell,
                pbc:       data.pbc,
                natoms:    data.natoms + shellData.natoms
              }};
              const fr = crystalData.scaled_positions;
              const N  = crystalData.natoms;
              // --- 3. 原子筛选（按分数坐标 fr） ---
              const atomMap      = new Map(); // oldAtom -> newAtom
              const newPositions = [];
              const newFrac      = [];
              const newSymbols   = [];
              const newRadii     = [];
              const newColors    = [];
              const newCharges   = [];
              for (let i = 0; i < N; i++) {{
                if (insideCell(fr[i], 5e-2, nx, ny, nz)) {{
                  const newIndex = newPositions.length;
                  atomMap.set(i, newIndex);
                  newPositions.push(crystalData.positions[i]);
                  newFrac.push(fr[i]);
                  newSymbols.push(crystalData.symbols[i]);
                  newRadii.push(crystalData.radii[i]);
                  newColors.push(crystalData.colors[i]);
                  newCharges.push(crystalData.charges[i]);
                }}
              }}
              // --- 4. 合并 core + shell 实例（combInst 空间） ---
              const combCellXYZ    = [];
              const combCellOffset = [];
              const combS          = [];
              const combCellIndex  = [];
              const combBaseIndex  = [];
              // core
              for (let inst = 0; inst < core.baseIndex.length; inst++) {{
                const cell = core.cellIndex[inst];

                combCellXYZ.push(core.cellXYZ[cell]);
                combCellOffset.push([
                  core.cellOffset[cell * 3],
                  core.cellOffset[cell * 3 + 1],
                  core.cellOffset[cell * 3 + 2],
                ]);
                combS.push([
                  core.S[cell * 3],
                  core.S[cell * 3 + 1],
                  core.S[cell * 3 + 2],
                ]);
                combCellIndex.push(cell);
                combBaseIndex.push(core.baseIndex[inst]); // 指向 crystalData 原胞原子
              }}
              // shell
              for (let inst = 0; inst < shell.baseIndex.length; inst++) {{
                combCellXYZ.push(shell.cellXYZ[inst]);
                combCellOffset.push([
                  shell.cellOffset[inst * 3],
                  shell.cellOffset[inst * 3 + 1],
                  shell.cellOffset[inst * 3 + 2],
                ]);
                combS.push([
                  shell.S[inst * 3],
                  shell.S[inst * 3 + 1],
                  shell.S[inst * 3 + 2],
                ]);
                combCellIndex.push(shell.cellIndex[inst]);
                combBaseIndex.push(shell.baseIndex[inst]); // 指向 crystalData 壳胞原子
              }}

              const combInstCount = combBaseIndex.length;
              // --- 5. 实例筛选（用分数坐标 fr + S） ---
              const newCellXYZ    = [];
              const newCellOffset = [];
              const newS          = [];
              const newCellIndex  = [];
              const newBaseIndex  = [];
              const instMap       = new Map(); // combInst -> newInst

              for (let combInst = 0; combInst < combInstCount; combInst++) {{
                const oldAtom = combBaseIndex[combInst];
                const newAtom = atomMap.get(oldAtom);
                if (newAtom === undefined) continue;

                const fr0    = crystalData.scaled_positions[oldAtom]; // 原胞分数坐标
                const S_inst = combS[combInst];                       // [ox, oy, oz]

                const f_super = [
                  fr0[0] + S_inst[0],
                  fr0[1] + S_inst[1],
                  fr0[2] + S_inst[2],
                ];

                if (!insideCell(f_super, 5e-2, nx, ny, nz)) continue;

                const newInst = newCellXYZ.length;

                newCellXYZ[newInst]    = combCellXYZ[combInst];
                newCellOffset[newInst] = combCellOffset[combInst];
                newS[newInst]          = S_inst;
                newCellIndex[newInst]  = combCellIndex[combInst];
                newBaseIndex[newInst]  = newAtom; // 指向筛选后的新原子索引

                instMap.set(combInst, newInst);
              }}
              // --- 6. 扩胞 bonds（在 combInst 空间） ---
              const expandedBonds = [];

              for (let combInstA = 0; combInstA < combInstCount; combInstA++) {{
                const newInstA = instMap.get(combInstA);
                if (newInstA === undefined) continue;

                const i   = combBaseIndex[combInstA];
                const S_i = combS[combInstA];

                for (const b of crystalData.bonds) {{
                  if (b.i !== i) continue;

                  const j = b.j;

                  const S_j = [
                    S_i[0] + b.offset[0],
                    S_i[1] + b.offset[1],
                    S_i[2] + b.offset[2],
                  ];
                  // 在 combInst 空间找 instB
                  let combInstB = -1;
                  for (let k = 0; k < combInstCount; k++) {{
                    if (combBaseIndex[k] === j &&
                        combS[k][0] === S_j[0] &&
                        combS[k][1] === S_j[1] &&
                        combS[k][2] === S_j[2]) {{
                      combInstB = k;
                      break;
                    }}
                  }}
                  if (combInstB === -1) continue;

                  const newInstB = instMap.get(combInstB);
                  if (newInstB === undefined) continue;

                  expandedBonds.push({{ instA: newInstA, instB: newInstB, offset: b.offset }});
                }}
              }}
              // --- 6.5 构建 newInst -> combInst 的反向映射 ---
              const reverseInstMap = new Map();
              for (const [combInst, newInst] of instMap) {{
                reverseInstMap.set(newInst, combInst);
              }}
              // --- 7. 用分数坐标再次筛键（两端都在 supercell 内） ---
              const newBonds = [];

              for (const b of expandedBonds) {{
                const aInst = b.instA;
                const bInst = b.instB;

                const combInstA = reverseInstMap.get(aInst);
                const combInstB = reverseInstMap.get(bInst);

                const oldA = combBaseIndex[combInstA];
                const oldB = combBaseIndex[combInstB];

                const frA = crystalData.scaled_positions[oldA];
                const frB = crystalData.scaled_positions[oldB];

                const SA = newS[aInst];
                const SB = newS[bInst];

                const f_super_A = [frA[0] + SA[0], frA[1] + SA[1], frA[2] + SA[2]];
                const f_super_B = [frB[0] + SB[0], frB[1] + SB[1], frB[2] + SB[2]];

                if (!insideCell(f_super_A, 5e-2, nx, ny, nz)) continue;
                if (!insideCell(f_super_B, 5e-2, nx, ny, nz)) continue;

                newBonds.push(b);
              }}
              // --- 8. 计算 atomWorldPos ---
              const newAtomWorldPos = new Float32Array(newBaseIndex.length * 3);
              for (let inst = 0; inst < newBaseIndex.length; inst++) {{
                const a   = newBaseIndex[inst];   // 新原子索引
                const p   = newPositions[a];      // 原胞坐标
                const off = newCellOffset[inst];  // 偏移
                newAtomWorldPos[inst * 3]     = p[0] + off[0];
                newAtomWorldPos[inst * 3 + 1] = p[1] + off[1];
                newAtomWorldPos[inst * 3 + 2] = p[2] + off[2];
              }}
              // --- 9. 返回最终 crystal superData ---
              return {{
                P: new Float32Array(newPositions.flat()),
                atomWorldPos: newAtomWorldPos,

                baseIndex: new Uint32Array(newBaseIndex),
                cellIndex: new Uint32Array(newCellIndex),
                A: core.A,
                S: new Float32Array(newS.flat()),
                cellXYZ: newCellXYZ,
                cellOffset: new Float32Array(newCellOffset.flat()),
                superCell: core.superCell,

                N: atomMap.size,
                M: newBaseIndex.length,

                nx: core.nx,
                ny: core.ny,
                nz: core.nz,
                
                bonds: newBonds,
                call: "instanceBonds",

                data: {{
                  positions: newPositions,
                  scaled_positions: newFrac,
                  symbols: newSymbols,
                  radii: newRadii,
                  colors: newColors,
                  charges: newCharges,
                  bonds: crystalData.bonds,
                  cell: crystalData.cell,
                  pbc: crystalData.pbc,
                  natoms: atomMap.size
                }}
              }};
            }}
          }}
        }}
      }}
      
      // ===============================
      // 2. 渲染信息计算
      // ===============================
      // renderAtomsInstanced()——原子渲染信息转译
      function buildAtomRenderInfo(superData, data) {{
        const {{ atomWorldPos, baseIndex }} = superData;
        const total = baseIndex.length;

        const matrices = new Array(total);
        const colors   = new Float32Array(total * 4);

        const dummy = new THREE.Object3D();

        // 预计算颜色
        if (!data.atomColors) {{
          data.atomColors = data.colors.map(c => new THREE.Color(c));
        }}

        for (let inst = 0; inst < total; inst++) {{
          const base = baseIndex[inst];
          // 直接读取预计算坐标
          const x = atomWorldPos[inst*3];
          const y = atomWorldPos[inst*3+1];
          const z = atomWorldPos[inst*3+2];

          const r = data.radii[base] * 0.4;

          dummy.position.set(x, y, z);
          dummy.scale.set(r, r, r);
          dummy.updateMatrix();

          if (!matrices[inst]) matrices[inst] = new THREE.Matrix4();
          matrices[inst].copy(dummy.matrix);

          const c = data.atomColors[base];
          colors[inst*4]     = c.r;    //R
          colors[inst*4 + 1] = c.g;    //G
          colors[inst*4 + 2] = c.b;    //B
          colors[inst*4 + 3] = 1.0;    //Alpha
        }}

        return {{ matrices, colors }};
      }}
      // renderBondsInstanced()——键渲染信息转译(调度)
      function buildBondRenderInfo(superData, data) {{
        const mode = superData.call;   // "analyticalBonds" 或 "instanceBonds"
        if (mode === "instanceBonds") {{
          return renderInstanceBonds(superData);
        }} else if (mode === "analyticalBonds"){{
          return renderAnalyticalBonds(superData, data);
        }}
      }}
      // renderAnalyticalBonds()——键渲染信息转译(解析)
      function renderAnalyticalBonds(superData, data) {{
        const {{ atomWorldPos, baseIndex, cellXYZ}} = superData;
        const bonds = data.bonds.filter(b => data.charges[b.i] >= 0);
        const A = data.cell;
        // === 1. 按 cellXYZ 分组 ===
        // 预构建 instMap：O(1) 查找 instB
        const cellMap = new Map();
        for (let inst = 0; inst < baseIndex.length; inst++) {{
          const key = cellXYZ[inst].join("_");
          if (!cellMap.has(key)) cellMap.set(key, []);
          cellMap.get(key).push(inst);
        }}
        const cells = [...cellMap.values()];
        // === 2. 不预分配数组，直接 push（避免 undefined）===
        // 分配数组
        const matrices  = [];    //cylinder
        const matricesA = [];    //sphere A
        const matricesB = [];    //sphere B
        const colorA    = [];
        const colorB    = [];

        const dummy = new THREE.Object3D();
        const vA = new THREE.Vector3();
        const vB = new THREE.Vector3();
        const vDir = new THREE.Vector3();
        // 预计算颜色
        if (!data.atomColors) {{
          data.atomColors = data.colors.map(c => new THREE.Color(c));
        }}
        // 统一流程函数
        function applyMatrix(pos, target, sx, sy, sz, face) {{
          dummy.rotation.set(0, 0, 0);    //重置偏转
          dummy.position.copy(pos);    // 位置
          dummy.lookAt(target);    // 朝向
          if (face === 1) {{dummy.rotateY(Math.PI)}};    //如有需求，沿 Y 轴偏转180°
          dummy.rotateX(Math.PI / 2);    //沿 X 轴偏转90°
          dummy.scale.set(sx, sy, sz);    // 缩放
          dummy.updateMatrix();    // 传入矩阵(更新)
          return dummy.matrix.clone();    // 传入矩阵(递归)
        }}
        // === 3. 按 cell 渲染键 ===
        // 遍历所有实例，完整渲染所有键
        for (const instList of cells) {{
        for (const b of bonds) {{
          const {{ i, j, offset }} = b;
            // 正确查找 j 的实例：cellA + offset
            const instA = instList.find(inst => baseIndex[inst] === i);
            const instB = instList.find(inst => baseIndex[inst] === j);
            if (instA === undefined || instB === undefined) continue;
            // 直接读取 j 的世界坐标（已经包含 cellB 的平移）
            vA.fromArray(atomWorldPos, instA * 3);
            vB.fromArray(atomWorldPos, instB * 3);
            if (offset[0] || offset[1] || offset[2]) {{
              vB.x += offset[0]*A[0][0] + offset[1]*A[1][0] + offset[2]*A[2][0];
              vB.y += offset[0]*A[0][1] + offset[1]*A[1][1] + offset[2]*A[2][1];
              vB.z += offset[0]*A[0][2] + offset[1]*A[1][2] + offset[2]*A[2][2];
            }}
            // Cylinder
            vDir.subVectors(vB, vA);
            const L = vDir.length();
            const R = 0.1;
            // 按顺序写入
            matrices.push(applyMatrix(vA, vB, R, L, R, 0));
            matricesA.push(applyMatrix(vA, vB, R, R, R, 1));
            matricesB.push(applyMatrix(vB, vA, R, R, R, 1));

            const cA = data.atomColors[i];
            const cB = data.atomColors[j];

            colorA.push(cA.r, cA.g, cA.b, 1);
            colorB.push(cB.r, cB.g, cB.b, 1);
          }}
        }}
        //console.log("bonds.length =", data.bonds.length);
        //console.log("realBondCount =", matrices.length);
        return {{ 
          matrices, 
          matricesA, 
          matricesB, 
          colorA: new Float32Array(colorA), 
          colorB: new Float32Array(colorB) }};
      }}
      // renderInstanceBonds()——键渲染信息转译(实例)
      function renderInstanceBonds(superData) {{
        const {{ atomWorldPos, baseIndex, bonds, data }} = superData;
        const matrices  = [];
        const matricesA = [];
        const matricesB = [];
        const colorA    = [];
        const colorB    = [];
        const dummy = new THREE.Object3D();
        const vA = new THREE.Vector3();
        const vB = new THREE.Vector3();
        const vDir = new THREE.Vector3();
        if (!data.atomColors) {{
          data.atomColors = data.colors.map(c => new THREE.Color(c));
        }}
        function applyMatrix(pos, target, sx, sy, sz, face) {{
          dummy.rotation.set(0, 0, 0);
          dummy.position.copy(pos);
          dummy.lookAt(target);
          if (face === 1) dummy.rotateY(Math.PI);
          dummy.rotateX(Math.PI / 2);
          dummy.scale.set(sx, sy, sz);
          dummy.updateMatrix();
          return dummy.matrix.clone();
        }}
        for (const b of bonds) {{
          const instA = b.instA;
          const instB = b.instB;
          vA.fromArray(atomWorldPos, instA * 3);
          vB.fromArray(atomWorldPos, instB * 3);
          vDir.subVectors(vB, vA);
          const L = vDir.length();
          const R = 0.1;
          matrices.push(applyMatrix(vA, vB, R, L, R, 0));
          matricesA.push(applyMatrix(vA, vB, R, R, R, 1));
          matricesB.push(applyMatrix(vB, vA, R, R, R, 1));
          const cA = data.atomColors[ baseIndex[instA] ];
          const cB = data.atomColors[ baseIndex[instB] ];
          colorA.push(cA.r, cA.g, cA.b, 1);
          colorB.push(cB.r, cB.g, cB.b, 1);
        }}
        return {{
          matrices,
          matricesA,
          matricesB,
          colorA: new Float32Array(colorA),
          colorB: new Float32Array(colorB),
        }};
      }}
      
      // ===============================
      // 3. InstancedMesh 渲染层
      // ===============================
      // function buildInstancedMesh()——通用渲染内核
      function buildInstancedMesh(geometry, material, matrices, colorAttributes) {{
        const count = matrices.length;
        if (count === 0) {{
          // 返回一个空 Group，避免创建非法 InstancedMesh
          return new THREE.Group();
        }}
        const geom = geometry.clone();
        // 绑定颜色 attribute（可选）
        if (colorAttributes) {{
          for (const key in colorAttributes) {{
            const array = colorAttributes[key];
            const itemSize = array.length / count;  // 自动判断是 3 通道还是 4 通道
            // 只允许 1/2/3/4 且是整数，否则跳过这个 attribute
            if (!Number.isInteger(itemSize) || itemSize < 1 || itemSize > 4) {{
              console.warn(`Invalid itemSize for attribute ${{key}}:`, itemSize);
              continue;
            }}
            geom.setAttribute(
              key,
              new THREE.InstancedBufferAttribute(array, itemSize)
            );
          }}
        }}
        const instanced = new THREE.InstancedMesh(geom, material, count);
        instanced.instanceMatrix.setUsage(THREE.DynamicDrawUsage);  
        for (let i = 0; i < count; i++) {{
          instanced.setMatrixAt(i, matrices[i]);
        }}
        instanced.instanceMatrix.needsUpdate = true;
        return instanced;
      }}
      // renderAtomsInstanced()——原子渲染
      function renderAtomsInstanced(superData, data) {{
        const {{ matrices, colors }} = buildAtomRenderInfo(superData, data);
        
        const mesh = buildInstancedMesh(
          new THREE.SphereGeometry(1, 16, 16),
          atomMaterial,
          matrices,
          {{ instanceColor: colors }}
        );
        // 添加atoms字典，供 applyModelStyle() / applyCoordinationView() 查找
        mesh.name = "atoms";
        return mesh
      }}
      // renderBondsInstanced()——键渲染
      function renderBondsInstanced(superData, data) {{
        const {{ matrices, matricesA, matricesB, colorA, colorB }} = buildBondRenderInfo(superData, data);
        // Cylinder（键身）
        const cylGeom = new THREE.CylinderGeometry(1, 1, 1, 12, 1, true).translate(0, 0.5, 0);
        const meshCyl = buildInstancedMesh(
          cylGeom,
          bondMaterial,
          matrices,
          {{ colorA, colorB }}
        );
        meshCyl.name = "bonds_cyl";
        // Hemisphere（半球头）
        const hemisphereGeom = new THREE.SphereGeometry(
          1,          // 半径
          12,           // 水平分段
          12,           // 垂直分段
          0, Math.PI*2, // 经度范围
          0, Math.PI/2  // 纬度范围（半球）
        );
        // SphereA
        const meshA = buildInstancedMesh(
          hemisphereGeom,
          hemisphereMaterial,
          matricesA,
          {{ instanceColor: colorA }}
        );
        meshA.name = "bonds_sphereA";
        // SphereB
        const meshB = buildInstancedMesh(
          hemisphereGeom,
          hemisphereMaterial,
          matricesB,
          {{ instanceColor: colorB }}
        );
        meshB.name = "bonds_sphereB";
        // 合并化学键模型
        const group = new THREE.Group();
          group.add(meshCyl);
          group.add(meshA);
          group.add(meshB);
        // 添加bonds字典，供 applyModelStyle() / applyCoordinationView() 查找
        group.name = "bonds";
        return group
      }}

      // ===============================
      // 4. 晶胞框架 + 坐标轴
      // ===============================
      // createCellFrame()
      function createCellFrame(cell) {{
        const a = new THREE.Vector3(...cell[0]);
        const b = new THREE.Vector3(...cell[1]);
        const c = new THREE.Vector3(...cell[2]);

        const O  = new THREE.Vector3(0,0,0);
        const A  = a.clone();
        const B  = b.clone();
        const C  = c.clone();
        const AB = a.clone().add(b);
        const AC = a.clone().add(c);
        const BC = b.clone().add(c);
        const ABC = a.clone().add(b).add(c);

        const pts = [
          O,A,  O,B,  O,C,
          A,AB, A,AC,
          B,AB, B,BC,
          C,AC, C,BC,
          AB,ABC,
          AC,ABC,
          BC,ABC
        ];

        const geom = new THREE.BufferGeometry().setFromPoints(pts);
        const atomMaterial = new THREE.LineBasicMaterial({{ color: 0x000000 }});
        return new THREE.LineSegments(geom, atomMaterial);
      }}
      // createCrystalAxes()
      function createCrystalAxes(cell, axisLength = 10) {{
        const a = new THREE.Vector3(...cell[0]).normalize().multiplyScalar(axisLength);
        const b = new THREE.Vector3(...cell[1]).normalize().multiplyScalar(axisLength);
        const c = new THREE.Vector3(...cell[2]).normalize().multiplyScalar(axisLength);

        const axes = new THREE.Group();
        // 调节箭头长宽
        const headLength = axisLength * 0.10;    // 箭头头部长度
        const headWidth  = axisLength * 0.05;    // 箭头头部宽度
        axes.add(
          new THREE.ArrowHelper(
            a.clone().normalize(),    //方向向量
            new THREE.Vector3(0,0,0),    //起点
            axisLength,    //箭头总长度
            0xff0000,    //颜色
            headLength,    //箭头头部长度
            headWidth   // 箭头头部宽度
        ));
        axes.add(
          new THREE.ArrowHelper(
            b.clone().normalize(), 
            new THREE.Vector3(0,0,0), 
            axisLength, 
            0x00ff00, 
            headLength, 
            headWidth
          ));
        axes.add(new THREE.ArrowHelper(
          c.clone().normalize(), 
          new THREE.Vector3(0,0,0),
            axisLength, 
            0x0000ff, 
            headLength, 
            headWidth
          ));

        return axes;
      }}

      // ===============================
      // 5. 测量辅助展示效果
      // ===============================
      // updateHighlights()——高亮选择的原子
      function updateHighlights(superData, data) {{
        // 隐藏所有球
        for (let i = 0; i < 4; i++) {{
          const depthSphere = highlightGroup.children[i*2];
          const shellSphere = highlightGroup.children[i*2+1];
          depthSphere.visible = false;
          shellSphere.visible = false;
        }}
        // 更新选中的球
        for (let i = 0; i < pickedAtoms.length; i++) {{

          const id = pickedAtoms[i];
          const pos = getAtomPosition(superData, id);

          const baseIndex = superData.baseIndex[id];
          const r = data.radii[baseIndex] * 0.4 * 1.2;

          const depthSphere = highlightGroup.children[i*2];
          const shellSphere = highlightGroup.children[i*2+1];

          depthSphere.position.copy(pos);
          shellSphere.position.copy(pos);

          depthSphere.scale.set(r, r, r);
          shellSphere.scale.set(r, r, r);

          depthSphere.renderOrder = 0;   
          shellSphere.renderOrder = 1;   

          depthSphere.visible = true;
          shellSphere.visible = true;
        }}
      }}
      // updateDashedLines()——虚线按顺序连接高亮原子
      function updateDashedLines(superData) {{
        // 清除虚线，初始函数
        while (lineGroup.children.length > 0) {{
          lineGroup.remove(lineGroup.children[0]);
        }}
        // 重新绘制虚线
        for (let i = 0; i < pickedAtoms.length - 1; i++) {{
          const idA = pickedAtoms[i];
          const idB = pickedAtoms[i+1];

          const A = getAtomPosition(superData, idA);
          const B = getAtomPosition(superData, idB);

          const geom = new THREE.BufferGeometry().setFromPoints([A, B]);
          const mat = new THREE.LineDashedMaterial({{
            color: 0x000000,
            transparent: true,
            opacity: 1.0,
            dashSize: 0.3,
            gapSize: 0.2
          }});

          const line = new THREE.Line(geom, mat);
          line.computeLineDistances();
          lineGroup.add(line);
        }}
      }}
      // drawDihedralTriangles()——闭合虚线绘制三角面
      function drawDihedralTriangles(superData) {{
        // 清空旧三角面
        while (triangleGroup.children.length > 0) {{
          triangleGroup.remove(triangleGroup.children[0]);
        }}
        // 重新三角面
        if (pickedAtoms.length < 4) return;

        const i = pickedAtoms[0];
        const j = pickedAtoms[1];
        const k = pickedAtoms[2];
        const l = pickedAtoms[3];

        const A = getAtomPosition(superData, i);
        const B = getAtomPosition(superData, j);
        const C = getAtomPosition(superData, k);
        const D = getAtomPosition(superData, l);

        // 三角面 1：A-B-C
        {{
          const geom = new THREE.BufferGeometry().setFromPoints([A, B, C]);
          geom.setIndex([0, 1, 2]);
          geom.computeVertexNormals();

          const mat = triangleMaterialTemplate.clone();
          mat.uniforms.uColor.value.set(0xff8800);

          const mesh = new THREE.Mesh(geom, mat);
          triangleGroup.add(mesh);
        }}

        // 三角面 2：B-C-D
        {{
          const geom = new THREE.BufferGeometry().setFromPoints([B, C, D]);
          geom.setIndex([0, 1, 2]);
          geom.computeVertexNormals();

          const mat = triangleMaterialTemplate.clone();
          mat.uniforms.uColor.value.set(0x0088ff);

          const mesh = new THREE.Mesh(geom, mat);
          triangleGroup.add(mesh);
        }}
      }}

      // ===============================
      // 6. 交互层（点击拾取）
      // ===============================
      // getAtomPosition()——拾取原子
      function getAtomPosition(superData, instanceId) {{
        const p = superData.atomWorldPos;
        return new THREE.Vector3(
          p[instanceId*3],
          p[instanceId*3+1],
          p[instanceId*3+2]
        );
      }}
      let raycaster = new THREE.Raycaster();
      let mouse = new THREE.Vector2();
      let clickTimer = null;
      // setupPicking()——点击类型判断
      function setupPicking(renderer, camera, scene) {{
        renderer.domElement.addEventListener("pointerdown", (event) => {{
          if (clickTimer) {{
            clearTimeout(clickTimer);
            clickTimer = null;
            handleDoubleClick(event, renderer, camera, scene);
          }} else {{
            clickTimer = setTimeout(() => {{
              clickTimer = null;
              // 单击：不做任何事
            }}, 200);
          }}
        }});
      }}
      // handleDoubleClick()——双击执行
      function handleDoubleClick(event, renderer, camera, scene) {{
          const rect = renderer.domElement.getBoundingClientRect();
          mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
          mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

          raycaster.setFromCamera(mouse, camera);
          // 每次启动取最新声子数据
          const ph = root.api.phonon;
          // 每次启动取最新 superData 数据
          const superData = root.api.superData;  
          // 1. 优先拾取声子箭头
          if (ph.enabled) {{
            const arrows = root.getObjectByName("arrows");
            if (arrows) {{
              const arrowHits = raycaster.intersectObject(arrows, true);
              for (let hit of arrowHits) {{
                if (hit.instanceId !== undefined) {{
                  onPhononArrowClick(hit.instanceId, superData);
                  return;
                }}
              }}
            }}
          }}
          // 2. 拾取原子
          const atoms = root.getObjectByName("atoms");
          if (!atoms) return;
          const hits = raycaster.intersectObject(atoms, true);
          for (let hit of hits) {{
            if (hit.instanceId !== undefined) {{
              onAtomDoubleClick(hit.instanceId, superData);
              return;
            }}
          }}
          // 点击空白 → 清空
          resetPicking();
      }}
      // resetPicking()——点击空白
      function resetPicking() {{
        pickedAtoms = [];
        // 清除所有高亮球
        highlightGroup.children.forEach(s => s.visible = false);
        // 清除虚线
        while (lineGroup.children.length > 0) {{
          lineGroup.remove(lineGroup.children[0]);
        }}
        // 清空三角面
        while (triangleGroup.children.length > 0) {{
          triangleGroup.remove(triangleGroup.children[0]);
        }}
        // 清空声子轨迹
        const ph = root.api.phonon;
        if (ph.selectedAtoms && ph.selectedAtoms.length > 0) {{
          ph.selectedAtoms.forEach(id => {{
            const obj = root.getObjectByName(`ellipse_${{id}}`);
            if (obj) root.remove(obj);
          }});
          ph.selectedAtoms = [];   // 清空队列
        }}
        root.api.appendResult("计算终止"); // 清空结果
      }}
      let pickedAtoms = [];  // 存 instanceId
      // onAtomDoubleClick()——点击原子执行对应动作输出
      function onAtomDoubleClick(instanceId, superData) {{
        const data = superData.data;
        // 第 5 个原子 → 自动重置
        if (pickedAtoms.length >= 4) {{
          resetPicking();
        }}
        pickedAtoms.push(instanceId);
        updateHighlights(superData, data);
        updateDashedLines(superData);
        drawDihedralTriangles(superData);
        // 1 个原子 → 显示分数坐标
        if (pickedAtoms.length === 1) {{
          const pos = getAtomPosition(superData, instanceId);
          const frac = cartesianToFractional(pos, data.cell);
          const symbol = data.symbols[superData.baseIndex[instanceId]];

          const msg = 
            `原子 ${{instanceId}} (${{symbol}})\\n` +
            `笛卡尔坐标 = (${{pos.x.toFixed(4)}}, ${{pos.y.toFixed(4)}}, ${{pos.z.toFixed(4)}})\\n` +
            `分数坐标 = (${{frac.x.toFixed(4)}}, ${{frac.y.toFixed(4)}}, ${{frac.z.toFixed(4)}})`;

          console.log(msg);
          root.api.appendResult(msg);
          return;
        }}
        // 2 个 → 键长
        if (pickedAtoms.length === 2) {{
          measureDistance(superData, data);
        }}
        // 3 个 → 键角
        else if (pickedAtoms.length === 3) {{
          measureAngle(superData, data);
        }}
        // 4 个 → 二面角
        else if (pickedAtoms.length === 4) {{
          measureDihedral(superData, data);
        }}
      }}
      // onPhononArrowClick()——点击箭头输出该原子声子信息
      function onPhononArrowClick(instanceId, superData) {{
        const ph = root.api.phonon;
        const data = superData.data;
        // 如果未启用声子模式则停止运行
        if (!ph.enabled || !ph.instDispR || !ph.instDispI) return;
        // 如果点击的是已选中的原子 → 取消该原子的轨迹
        if (ph.selectedAtoms.includes(instanceId)) {{
          // 删除轨迹对象
          const obj = root.getObjectByName(`ellipse_${{instanceId}}`);
          if (obj) root.remove(obj);
          // 从列表移除
          ph.selectedAtoms = ph.selectedAtoms.filter(id => id !== instanceId);
          root.api.appendResult(`已取消原子 ${{instanceId}} 的声子轨迹`);
          console.log(`取消原子 ${{instanceId}} 的声子轨迹`);
          return;
        }}
        // 如果超过 10 个 → 清空所有轨迹并重新开始
        if (ph.selectedAtoms.length >= ph.maxSelected) {{
          // 清空所有轨迹
          ph.selectedAtoms.forEach(id => {{
            const obj = root.getObjectByName(`ellipse_${{id}}`);
            if (obj) root.remove(obj);
          }});
          ph.selectedAtoms = []; // 重置队列
          root.api.appendResult("轨迹数量超过 10 个，已自动清空");
          console.log("轨迹数量超过 10 个，已自动清空");
        }}
        // 添加新的原子
        ph.selectedAtoms.push(instanceId);
        // 创建单原子轨迹
        const traj = renderEllipseTrajectories(
          ph.basePos,
          ph.instDispR,
          ph.instDispI,
          ph.amplitude,
          instanceId
        );
        traj.name = `ellipse_${{instanceId}}`;
        root.add(traj);
        // 获取本征向量实部
        const dxR = ph.instDispR[instanceId*3];
        const dyR = ph.instDispR[instanceId*3+1];
        const dzR = ph.instDispR[instanceId*3+2];
        // 获取本征向量虚部
        const dxI = ph.instDispI[instanceId*3];
        const dyI = ph.instDispI[instanceId*3+1];
        const dzI = ph.instDispI[instanceId*3+2];
        // 获取元素符号
        const symbol = data.symbols[superData.baseIndex[instanceId]];
        // 统一数据格式
        function formatComplex(re, im) {{
          // 实部：正数 → "  0.1234"，负数 → " -0.1234"
          const reStr = (re >= 0 ? "+" : "-") + Math.abs(re).toFixed(4);
          // 虚部：正数 → "+ 0.1234"，负数 → "- 0.1234"
          const imStr = (im >= 0 ? "+ " : "- ") + Math.abs(im).toFixed(4);
          return `${{reStr}}  ${{imStr}}`;
        }}
        // 1. 先生成三行内容
        const rows = [formatComplex(dxR, dxI), formatComplex(dyR, dyI), formatComplex(dzR, dzI)];
        // 2. 找出最长行
        const maxLen = Math.max(...rows.map(r => r.length));
        // 3. 统一填充到相同宽度（整行对齐）
        const [r1, r2, r3] = rows.map(r => r.padStart(maxLen));
        // 4. 拼接成矩阵格式
        const msg =
          `原子 ${{instanceId}} (${{symbol}}) 的本征向量（复数列向量）：\\n` +
          `⎡ ${{r1}}i ⎤\\n` +
          `⎢ ${{r2}}j ⎥\\n` +
          `⎣ ${{r3}}k ⎦`;
        root.api.appendResult(msg);
        console.log(msg);
      }}
      // measureDistance()——键长计算结果输出
      function measureDistance(superData, data) {{
        const i = pickedAtoms[0];
        const j = pickedAtoms[1];

        const A = getAtomPosition(superData, i);
        const B = getAtomPosition(superData, j);

        const frac = cartesianToFractional(B, data.cell);
        const d = distancePBC(A, B, data.cell);
        const raw = rawVector(A, B).length();

        const symI = data.symbols[superData.baseIndex[i]];
        const symJ = data.symbols[superData.baseIndex[j]];

        const msg = 
          `原子 ${{j}} (${{symJ}})\\n` +
          `笛卡尔坐标 = (${{B.x.toFixed(4)}}, ${{B.y.toFixed(4)}}, ${{B.z.toFixed(4)}})\\n` + 
          `分数坐标 = (${{frac.x.toFixed(4)}}, ${{frac.y.toFixed(4)}}, ${{frac.z.toFixed(4)}})\\n` +
          `真实键长(${{symI}}(${{i}}), ${{symJ}}(${{j}})) = ${{raw.toFixed(4)}} Å\\n` +
          `warp键长(${{symI}}(${{i}}), ${{symJ}}(${{j}})) = ${{d.toFixed(4)}} Å`;

        console.log(msg);
        root.api.appendResult(msg);
      }}
      // measureAngle()——键角计算结果输出
      function measureAngle(superData, data) {{
        const i = pickedAtoms[0];
        const j = pickedAtoms[1];
        const k = pickedAtoms[2];

        const A = getAtomPosition(superData, i);
        const B = getAtomPosition(superData, j);
        const C = getAtomPosition(superData, k);

        const frac = cartesianToFractional(C, data.cell);
        const ang = anglePBC(A, B, C, data.cell);
        const raw = angleRaw(A, B, C)

        const symI = data.symbols[superData.baseIndex[i]];
        const symJ = data.symbols[superData.baseIndex[j]];
        const symK = data.symbols[superData.baseIndex[k]];


        const msg = 
          `原子 ${{k}} (${{symK}})\\n` + 
          `笛卡尔坐标 = (${{C.x.toFixed(4)}}, ${{C.y.toFixed(4)}}, ${{C.z.toFixed(4)}})\\n` + 
          `分数坐标 = (${{frac.x.toFixed(4)}}, ${{frac.y.toFixed(4)}}, ${{frac.z.toFixed(4)}})\\n` +
          `真实键角(${{symI}}(${{i}}), ${{symJ}}(${{j}}), ${{symK}}(${{k}})) = ${{raw.toFixed(2)}}°\\n` +
          `warp键角(${{symI}}(${{i}}), ${{symJ}}(${{j}}), ${{symK}}(${{k}})) = ${{ang.toFixed(2)}}°`;
        console.log(msg);
        root.api.appendResult(msg);
      }}
      // measureDihedral()——二面角计算结果输出
      function measureDihedral(superData, data) {{
        const i = pickedAtoms[0];
        const j = pickedAtoms[1];
        const k = pickedAtoms[2];
        const l = pickedAtoms[3];

        const A = getAtomPosition(superData, i);
        const B = getAtomPosition(superData, j);
        const C = getAtomPosition(superData, k);
        const D = getAtomPosition(superData, l);

        const frac = cartesianToFractional(D, data.cell);
        const dih = dihedralPBC(A, B, C, D, data.cell);
        const raw = dihedralRaw(A, B, C, D);

        const symI = data.symbols[superData.baseIndex[i]];
        const symJ = data.symbols[superData.baseIndex[j]];
        const symK = data.symbols[superData.baseIndex[k]];
        const symL = data.symbols[superData.baseIndex[l]];


        const msg = 
          `原子 ${{l}} (${{symL}})\\n` + 
          `笛卡尔坐标 = (${{D.x.toFixed(4)}}, ${{D.y.toFixed(4)}}, ${{D.z.toFixed(4)}})\\n` + 
          `分数坐标 = (${{frac.x.toFixed(4)}}, ${{frac.y.toFixed(4)}}, ${{frac.z.toFixed(4)}})\\n` +
          `真实二面角(${{symI}}(${{i}}), ${{symJ}}(${{j}}), ${{symK}}(${{k}}), ${{symL}}(${{l}})) = ${{raw.toFixed(2)}}°\\n` +
          `warp二面角(${{symI}}(${{i}}), ${{symJ}}(${{j}}), ${{symK}}(${{k}}), ${{symL}}(${{l}})) = ${{dih.toFixed(2)}}°`;
        console.log(msg);
        root.api.appendResult(msg);
      }}

      // ===============================
      // 7. 计算层（坐标/键长/键角/二面角 + PBC）
      // ===============================
      // cartesianToFractional()——原子坐标
      function cartesianToFractional(pos, cell) {{
        const a = new THREE.Vector3(...cell[0]);
        const b = new THREE.Vector3(...cell[1]);
        const c = new THREE.Vector3(...cell[2]);

        const M = new THREE.Matrix3();
        M.set(
          a.x, b.x, c.x,
          a.y, b.y, c.y,
          a.z, b.z, c.z
        );

        const Minv = new THREE.Matrix3().copy(M).invert();

        const frac = pos.clone().applyMatrix3(Minv);
        return frac;
      }}
      //vectorPBC()——PBC计算基础
      function vectorPBC(A, B, cell) {{
        // 构造晶胞矩阵 M
        const M = new THREE.Matrix3().set(
          cell[0][0], cell[1][0], cell[2][0],
          cell[0][1], cell[1][1], cell[2][1],
          cell[0][2], cell[1][2], cell[2][2]
        );

        // M 的逆矩阵
        const Minv = new THREE.Matrix3().copy(M).invert();

        // 转到分数坐标
        const Af = A.clone().applyMatrix3(Minv);
        const Bf = B.clone().applyMatrix3(Minv);

        // wrap 最近镜像
        const df = Bf.sub(Af);
        df.x -= Math.round(df.x);
        df.y -= Math.round(df.y);
        df.z -= Math.round(df.z);

        // 转回笛卡尔
        df.applyMatrix3(M);

        return df;
      }}
      //rawVector()——真实键长
      function rawVector(A, B) {{
        return B.clone().sub(A);
      }}
      // distancePBC()——warp键长
      function distancePBC(A, B, cell) {{
        return vectorPBC(A, B, cell).length();
      }}
      //angleRaw()——真实键长
      function angleRaw(A, B, C) {{
        const BA = rawVector(B, A);
        const BC = rawVector(B, C);

        return BA.angleTo(BC) * 180 / Math.PI;
      }}
      // anglePBC()——warp键角
      function anglePBC(A, B, C, cell) {{
        const BA = vectorPBC(B, A, cell);
        const BC = vectorPBC(B, C, cell);

        return BA.angleTo(BC) * 180 / Math.PI;
      }}
      //dihedralRaw()——真实二面角
      function dihedralRaw(A, B, C, D) {{
        const AB = rawVector(A, B);
        const BC = rawVector(B, C);
        const CD = rawVector(C, D);

        const n1 = new THREE.Vector3().crossVectors(AB, BC).normalize();
        const n2 = new THREE.Vector3().crossVectors(BC, CD).normalize();

        const m1 = new THREE.Vector3().crossVectors(n1, BC.clone().normalize());

        const x = n1.dot(n2);
        const y = m1.dot(n2);

        return Math.atan2(y, x) * 180 / Math.PI;
      }}
      // dihedralPBC()——warp二面角
      function dihedralPBC(A, B, C, D, cell) {{
        const AB = vectorPBC(A, B, cell);
        const BC = vectorPBC(B, C, cell);
        const CD = vectorPBC(C, D, cell);

        const n1 = new THREE.Vector3().crossVectors(AB, BC).normalize();
        const n2 = new THREE.Vector3().crossVectors(BC, CD).normalize();

        const m1 = new THREE.Vector3().crossVectors(n1, BC.clone().normalize());

        const x = n1.dot(n2);
        const y = m1.dot(n2);

        return Math.atan2(y, x) * 180 / Math.PI;
      }}

      // ===============================
      // 8. Three.js 初始化
      // ===============================
      const container = document.getElementById('viewer');

      const scene = new THREE.Scene();
      scene.background = new THREE.Color(0xffffff);
      // 正交相机
      const aspect = container.clientWidth / container.clientHeight;
      const camera = new THREE.OrthographicCamera(
        -10 * aspect, 10 * aspect,
        10, -10,
        0.1, 1000
      );
      camera.position.set(20, 20, 20);
      // 渲染器
      const renderer = new THREE.WebGLRenderer({{ antialias: true }});
      renderer.setSize(container.clientWidth, container.clientHeight);
      container.appendChild(renderer.domElement);
      // 控制器
      const controls = new OrbitControls(camera, renderer.domElement);
      controls.enableDamping = true;
      // root：所有结构都挂在这里
      const root = new THREE.Group();
      scene.add(root);

      // ===============================
      // 9. 材质初始化
      // ===============================
      // 创建 depthMaskMaterial 初始化高亮材质及光照，使 instanceColor 可被正常读取
      const depthMaskMaterial = new THREE.MeshBasicMaterial({{
        colorWrite: false,
        depthWrite: true,
        depthTest: false
      }});
      // 创建 highlightMateria 初始化深度遮罩层材质，不写颜色，只写深度，配合双通道渲染使用
      const highlightMaterial = new THREE.ShaderMaterial({{
        uniforms: {{
        uColor: {{ value: new THREE.Color(0xffff00) }},
        uAlpha: {{ value: 0.5 }}
      }},
      vertexShader: `
        varying vec3 vNormal;
        void main() {{
          vNormal = normal;
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }}
      `,
      fragmentShader: `
        uniform vec3 uColor;
        uniform float uAlpha;
        varying vec3 vNormal;

        void main() {{
          vec3 base = uColor;

          vec3 lightDir = normalize(vec3(0.4, 0.8, 0.6));
          vec3 viewDir  = normalize(vec3(0.0, 0.0, 1.0));

          vec3 ambient = base * 0.45;

          float diff = 0.5 + 0.5 * dot(vNormal, lightDir);
          vec3 diffuse = base * diff * 0.55;

          float rim = pow(1.0 - dot(vNormal, viewDir), 2.0);
          vec3 rimLight = base * rim * 0.35;

          vec3 halfDir = normalize(lightDir + viewDir);
          float spec = pow(max(dot(vNormal, halfDir), 0.0), 32.0);
          vec3 specular = vec3(1.0) * spec * 0.25;

          vec3 finalColor = ambient + diffuse + rimLight + specular;

          gl_FragColor = vec4(finalColor, uAlpha);
        }}
      `,
      transparent: true,
      depthWrite: false,
      depthTest: true,
      side: THREE.DoubleSide,
      lights: false
    }});
      // 创建 triangleMaterialTemplate 初始化三角面材质及光照，使 instanceColor 可被正常读取
      const triangleMaterialTemplate = new THREE.ShaderMaterial({{
        uniforms: {{
        uColor: {{ value: new THREE.Color() }},
        uAlpha: {{ value: 0.3 }}
      }},
      vertexShader: `
        varying vec3 vNormal;
        void main() {{
          vNormal = normal;
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }}
      `,
      fragmentShader: `
        uniform vec3 uColor;
        uniform float uAlpha;
        varying vec3 vNormal;

        void main() {{
          vec3 base = uColor;

          vec3 lightDir = normalize(vec3(0.4, 0.8, 0.6));
          vec3 viewDir  = normalize(vec3(0.0, 0.0, 1.0));

          vec3 ambient = base * 0.45;

          float diff = 0.5 + 0.5 * dot(vNormal, lightDir);
          vec3 diffuse = base * diff * 0.55;

          float rim = pow(1.0 - dot(vNormal, viewDir), 2.0);
          vec3 rimLight = base * rim * 0.35;

          vec3 halfDir = normalize(lightDir + viewDir);
          float spec = pow(max(dot(vNormal, halfDir), 0.0), 32.0);
          vec3 specular = vec3(1.0) * spec * 0.25;

          vec3 finalColor = ambient + diffuse + rimLight + specular;

          gl_FragColor = vec4(finalColor, uAlpha);
        }}
      `,
      transparent: true,
      depthWrite: false,
      depthTest: true,
      side: THREE.DoubleSide,
      lights: false
    }});
      // 初始化高亮球组
      const highlightGroup = new THREE.Group();
      scene.add(highlightGroup);
      // 球壳几何体
      const highlightGeo = new THREE.IcosahedronGeometry(1, 3);
      // 预创建 4 个高亮球
      for (let i = 0; i < 4; i++) {{
        // 深度遮罩球
        const depthSphere = new THREE.Mesh(highlightGeo, depthMaskMaterial);
        depthSphere.visible = false;
        highlightGroup.add(depthSphere);

        // 半透明外壳球
        const shellSphere = new THREE.Mesh(highlightGeo, highlightMaterial.clone());
        shellSphere.visible = false;
        highlightGroup.add(shellSphere);
      }}
      // 初始化虚线
      const lineGroup = new THREE.Group();
      scene.add(lineGroup);
      // 初始化三角面
      const triangleGroup = new THREE.Group();
      scene.add(triangleGroup);
      // 创建 ShaderMaterial 初始化原子材质及光照，使 instanceColor 可被正常读取
      const atomMaterial = new THREE.ShaderMaterial({{
        vertexShader: `
          attribute vec4 instanceColor;
          varying vec4 vColor;
          varying vec3 vNormal;

          void main() {{
            vColor = instanceColor;
            // 法线
            vNormal = normalize(normalMatrix * normal);
            // instanceMatrix 由 Three.js 自动注入
            vec4 worldPosition = instanceMatrix * vec4(position, 1.0);
            gl_Position = projectionMatrix * modelViewMatrix * worldPosition;
          }}
        `,
        fragmentShader: `
          varying vec4 vColor;
          varying vec3 vNormal;

          void main() {{
            // 降低饱和度
            vec3 baseColor = mix(vColor.rgb, vec3(0.8), 0.25);
            // 环境光
            vec3 ambient = baseColor.rgb * 0.30;
            // 主光方向
            vec3 lightDir = normalize(vec3(0.5, 1.0, 0.8));
            // 漫反射
            float diff = max(dot(vNormal, lightDir), 0.0);
            vec3 diffuse = baseColor.rgb * diff * 0.75;
            // 柔和边缘光
            float rim = pow(1.0 - max(dot(vNormal, lightDir), 0.0), 2.0);
            vec3 rimLight = baseColor.rgb * rim * 0.45;
            // 边缘阴影
            float edgeShadow = pow(max(dot(vNormal, lightDir), 0.0), 3.0);
            vec3 shadowTerm = baseColor.rgb * edgeShadow * 0.15;
            // 微弱金属高光
            vec3 viewDir = normalize(vec3(0.0, 0.0, 1.0));
            vec3 halfDir = normalize(lightDir + viewDir);
            float spec = pow(max(dot(vNormal, halfDir), 0.0), 32.0);
            vec3 specular = vec3(1.0) * spec * 0.35;
            // 综合渲染效果
            vec3 finalColor = ambient + diffuse + rimLight - shadowTerm + specular;
            // 修正颜色输出
            gl_FragColor = vec4(finalColor, vColor.a);
          }}
        `,
        transparent: true,                // 允许透明
        blending: THREE.NormalBlending,   // 正常混合模式
        lights: false
      }});
      // 创建 ShaderMaterial 初始化键本体材质及光照，使 instanceColor 可被正常读取
      const bondMaterial = new THREE.ShaderMaterial({{
        vertexShader: `
          attribute vec4 colorA;
          attribute vec4 colorB;
          varying vec4 vColorA;
          varying vec4 vColorB;
          varying vec2 vUv;
          varying vec3 vNormal;

          void main() {{
            vUv = uv;
            vColorA = colorA;
            vColorB = colorB;
            // 法线
            vNormal = normalize(normalMatrix * normal);
            // instanceMatrix 由 Three.js 自动注入
            vec4 worldPosition = instanceMatrix * vec4(position, 1.0);
            gl_Position = projectionMatrix * modelViewMatrix * worldPosition;
          }}
        `,
        fragmentShader: `
          varying vec2 vUv;
          varying vec4 vColorA;
          varying vec4 vColorB;
          varying vec3 vNormal;

          void main() {{
            // 一半一半颜色
            float t = step(0.5, vUv.y);
            vec4 baseColor = mix(vColorA, vColorB, t);
            // 降低饱和度
            baseColor.rgb = mix(baseColor.rgb, vec3(0.8), 0.25);
            // 环境光
            vec3 ambient = baseColor.rgb * 0.40;
            // 主光方向
            vec3 lightDir = normalize(vec3(0.5, 1.0, 0.8));
            // 漫反射
            float diff = max(dot(vNormal, lightDir), 0.0);
            vec3 diffuse = baseColor.rgb  * diff * 0.65;
            // 边缘光
            float rim = pow(1.0 - max(dot(vNormal, lightDir), 0.0), 2.0);
            vec3 rimLight = baseColor.rgb  * rim * 0.60;
            // 边缘阴影
            float edgeShadow = pow(max(dot(vNormal, lightDir), 0.0), 3.0);
            vec3 shadowTerm = baseColor.rgb * edgeShadow * 0.15;
            // 微弱金属高光
            vec3 viewDir = normalize(vec3(0.0, 0.0, 1.0));
            vec3 halfDir = normalize(lightDir + viewDir);
            float spec = pow(max(dot(vNormal, halfDir), 0.0), 32.0);
            vec3 specular = vec3(1.0) * spec * 0.45;
            // 综合渲染效果
            vec3 finalColor = ambient + diffuse + rimLight - shadowTerm + specular;
            // 修正颜色输出
            gl_FragColor = vec4(finalColor, baseColor.a);
          }}
        `,
        transparent: true,
        blending: THREE.NormalBlending,
        lights: false,
      }});
      // 创建 ShaderMaterial 初始化键圆头材质及光照，使 instanceColor 可被正常读取
      const hemisphereMaterial = new THREE.ShaderMaterial({{
        vertexShader: `
          attribute vec4 instanceColor;
          varying vec4 vColor;
          varying vec3 vNormal;

          void main() {{
            vColor = instanceColor;
            // 法线
            vNormal = normalize(normalMatrix * normal);
            // instanceMatrix 由 Three.js 自动注入
            vec4 worldPosition = instanceMatrix * vec4(position, 1.0);
            gl_Position = projectionMatrix * modelViewMatrix * worldPosition;
          }}
        `,
        fragmentShader: `
          varying vec4 vColor;
          varying vec3 vNormal;

          void main() {{
            // 降低饱和度
            vec3 baseColor = mix(vColor.rgb, vec3(0.8), 0.25);
            // 环境光
            vec3 ambient = baseColor.rgb * 0.40;
            // 主光方向
            vec3 lightDir = normalize(vec3(0.5, 1.0, 0.8));
            // 漫反射
            float diff = max(dot(vNormal, lightDir), 0.0);
            vec3 diffuse = baseColor.rgb * diff * 0.65;
            // 柔和边缘光
            float rim = pow(1.0 - max(dot(vNormal, lightDir), 0.0), 2.0);
            vec3 rimLight = baseColor.rgb * rim * 0.60;
            // 微弱金属高光
            vec3 viewDir = normalize(vec3(0.0, 0.0, 1.0));
            vec3 halfDir = normalize(lightDir + viewDir);
            float spec = pow(max(dot(vNormal, halfDir), 0.0), 32.0);
            vec3 specular = vec3(1.0) * spec * 0.45;
            // 综合渲染效果
            vec3 finalColor = ambient + diffuse + rimLight + specular;
            // 修正颜色输出
            gl_FragColor = vec4(finalColor, vColor.a);
          }}
        `,
        transparent: true,                // 允许透明
        blending: THREE.NormalBlending,   // 正常混合模式
        lights: false
      }});
      // 创建 ShaderMaterial 初始化多面体材质及光照，使 instanceColor 可被正常读取
      const polyMaterial = new THREE.ShaderMaterial({{
        uniforms: {{
        uColor: {{ value: new THREE.Color() }},
        uAlpha: {{ value: 0.35 }}
        }},
        vertexShader: `
          varying vec3 vNormal;

          void main() {{
            vNormal = normal;
            gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
          }}
        `,
        fragmentShader: `
          uniform vec3 uColor;
          uniform float uAlpha;
          varying vec3 vNormal;

          void main() {{
            vec3 base = mix(uColor, vec3(0.8), 0.25);
            // 主光方向
            vec3 lightDir = normalize(vec3(0.4, 0.8, 0.6));
            vec3 viewDir  = normalize(vec3(0.0, 0.0, 1.0));
            // 环境光
            vec3 ambient = base * 0.45;
            // 漫反射
            float diff = 0.5 + 0.5 * dot(vNormal, lightDir);
            vec3 diffuse = base * diff * 0.55;
            // 边缘阴影
            float rim = pow(1.0 - dot(vNormal, viewDir), 2.0);
            vec3 rimLight = base * rim * 0.35;
            // 微弱金属高光
            vec3 halfDir = normalize(lightDir + viewDir);
            float spec = pow(max(dot(vNormal, halfDir), 0.0), 32.0);
            vec3 specular = vec3(1.0) * spec * 0.25;
            // 综合渲染效果
            vec3 finalColor = ambient + diffuse + rimLight + specular;
            // 修正色彩输出
            gl_FragColor = vec4(finalColor, uAlpha);
          }}
        `,
        transparent: true,
        depthWrite: false,
        side: THREE.FrontSide,
        lights: false
      }});
      // 创建 ShaderMaterial 初始化箭头材质及光照，使 instanceColor 可被正常读取
      const arrowMaterial = new THREE.ShaderMaterial({{
        vertexShader: `
          varying vec3 vNormal;

          void main() {{
            vNormal = normalize(normalMatrix * normal);

            vec4 worldPosition = instanceMatrix * vec4(position, 1.0);
            gl_Position = projectionMatrix * modelViewMatrix * worldPosition;
          }}
        `,
        fragmentShader: `
          varying vec3 vNormal;

          void main() {{
            // 手动指定颜色（rgba）
            vec4 baseColor = vec4(0.7, 0.8, 0.9, 1.0);
            // 降低饱和度
            baseColor.rgb = mix(baseColor.rgb, vec3(0.8), 0.25);
            // 环境光
            vec3 ambient = baseColor.rgb * 0.40;
            // 主光方向
            vec3 lightDir = normalize(vec3(0.5, 1.0, 0.8));
            // 漫反射
            float diff = max(dot(vNormal, lightDir), 0.0);
            vec3 diffuse = baseColor.rgb * diff * 0.65;
            // 边缘光
            float rim = pow(1.0 - max(dot(vNormal, lightDir), 0.0), 2.0);
            vec3 rimLight = baseColor.rgb * rim * 0.60;
            // 边缘阴影
            float edgeShadow = pow(max(dot(vNormal, lightDir), 0.0), 2.0);
            vec3 shadowTerm = baseColor.rgb * edgeShadow * 0.20;
            // 微弱金属高光
            vec3 viewDir = normalize(vec3(0.0, 0.0, 1.0));
            vec3 halfDir = normalize(lightDir + viewDir);
            float spec = pow(max(dot(vNormal, halfDir), 0.0), 32.0);
            vec3 specular = vec3(1.0) * spec * 0.45;
            // 综合渲染效果
            vec3 finalColor = ambient + diffuse + rimLight - shadowTerm + specular;
            // 修正颜色输出
            gl_FragColor = vec4(finalColor, baseColor.a);
          }}
        `,
        transparent: true,
        blending: THREE.NormalBlending,
        lights: false,
      }});
      
      // ===============================
      // 10.初始化并开放root.api
      // ===============================
      // 添加默认root.state导入值
      root.state = new Proxy({{
        cellMode: "conventional",     // primitive / conventional
        chemistryMode: "crystal",     // crystal / coordination
        modelStyle: "ballstick",      // sphere / stick / ballstick
        showPolyhedron: false,        // 是否显示配位多面体
        nx: 1,    // a 轴扩胞系数
        ny: 1,    // b 轴扩胞系数
        nz: 1,    // c 轴扩胞系数
      }}, {{
        set(obj, key, value) {{
          obj[key] = value;
          // 自动触发渲染
          root.updateScene();
          return true;
        }}
      }});
      // 初始化root.api
      root.api = {{}};
      // 暴露 THREE
      root.api.THREE = THREE;
      // 暴露 camera / controls
      root.api.camera = camera;
      root.api.controls = controls;
      // 暴露 setRotation
      root.api.setRotation = (a, b, c) => {{
        root.rotation.set(a, b, c);
      }};
      // 晶胞轴先设为空
      root.api.a_axis = null;
      root.api.b_axis = null;
      root.api.c_axis = null;
      // 暴露超胞矩阵
      root.api.setSupercell = (nx, ny, nz) => {{
        // 1. 更新状态（自动触发渲染，因为 root.state 是 Proxy）
        root.state.nx = nx;
        root.state.ny = ny;
        root.state.nz = nz;
        // 2. 重新构建 supercell 数据（不渲染）
        root.api.superData = buildSupercore(data, nx, ny, nz);
        root.api.adj = buildAdjacencyList(data);
        // 3. 触发完整渲染（唯一入口）
        root.updateScene();
        // 4. 首次渲染触发 root-ready
        if (!root._readyFired) {{
          document.dispatchEvent(new CustomEvent("root-ready", {{ detail: {{ root }} }}));
          root._readyFired = true;
        }}
      }};
      // center 先设为空
      root.api.center = null;
      // 暴露 center
      function updateCenter() {{
        const box = new THREE.Box3().setFromObject(root);
        root.api.center = box.getCenter(new THREE.Vector3());
      }}
      // 暴露 msg 计算结果
      root.api.appendResult = function (msg) {{
        const div = document.createElement("div");    //创建<div>节点
        div.innerHTML = msg.replace(/\\n/g, "<br>");     //msg 转义为html放入
        // 触发事件，把 div 和 msg 暴露出去
        document.dispatchEvent(new CustomEvent("append-result", {{
          detail: {{ msg, div }}
        }}));
        return div;    //返回<div>节点
      }};
      // 暴露晶胞类型选择渲染器接口
      root.api.setCellMode = function(mode) {{
        root.state.cellMode = mode;
        //root.updateScene();
      }};
      // 暴露晶胞属性选择渲染器接口
      root.api.setChemistryMode = function(mode) {{
        root.state.chemistryMode = mode;
        //root.updateScene();
      }};
      // 暴露模型类型选择渲染器接口
      root.api.setModelStyle = function(style) {{
        root.state.modelStyle = style;
        //root.updateScene();
      }};
      // 暴露配位多面体渲染器接口
      root.api.togglePolyhedron = function(show) {{
        root.state.showPolyhedron = show;
        //root.updateScene();
      }};
      // 暴露渲染控制中心接口
      root.api.updateScene = () => root.updateScene();
      // 暴露声子模块控制接口
      root.api.phonon = {{
        enabled: false,   // 启用声子模式展示
        playing: false,   // 部分声子模式动画
        ellipseTrajs: null,   // 原子运动轨迹
        showTrajs: false,   // 展示原子运动轨迹
        amplitude: 5.0,   // 动画增幅倍率
        frequencyScale: 0.5,   // 动画周期
        phaseOffset: 0,   // 本征向量实部
        modeDispR: null,   // 本征向量实部
        modeDispI: null,   // 本征向量虚部
        instDispR: null,   // 扩胞后的本征向量实部
        instDispI: null,   // 扩胞后的本征向量虚部
        instPhase: null,   // 角动量
        omega: 0,   // 角动量
        modeIndex: 0,   // 本征向量实部
        basePos: null,   // 原子原始位置
        selectedAtoms: [],   // 选择原子列表
        maxSelected: 10,   // 列表上限
        // 切换声子模式
        enable() {{
          //console.log("ph.enable() called");
          this.enabled = true;
          // 声子模式刚开启 → 复制基准坐标
          const sd = root.api.superData;
          if (sd && sd.atomWorldPos) {{
            this.basePos = new Float32Array(sd.atomWorldPos);  // 静止坐标
            //console.log("basePos copied, length =", this.basePos.length);
          }} //else {{
            //console.log("superData not ready when enable() called");
          //}}
          initPhononMode(this.modeIndex);;
        }},
        disable() {{
          this.enabled = false;
          this.playing = false;
          this.reset();
        }},
        setMode(modeIndex) {{
          this.modeIndex = modeIndex;
          initPhononMode(modeIndex);
        }},
        // 播放/暂停
        togglePlay() {{
          this.playing = !this.playing;
          // 播放瞬间锁相，避免闪烁
          if (this.instPhase) {{
            const nowPhase = this.omega * performance.now() * 0.001;
            for (let i = 0; i < this.instPhase.length; i++) {{
              this.instPhase[i] = nowPhase;
            }}
          }}
        }},
        // 设置增幅
        setAmplitude(a) {{
          this.amplitude = a;
        }},
        // 设置频率倍率
        setFrequencyScale(f) {{
          this.frequencyScale = f;
          this.omega = 2 * Math.PI * this.frequencyScale;   // 实时更新角频率
        }},
        //
        toggleEllipse() {{
          this.showTrajs = !this.showTrajs;
          if (!this.showTrajs && this.ellipseTrajs) {{
            root.remove(this.ellipseTrajs);
            this.ellipseTrajs = null;
          }}
          root.updateScene();
        }},
        reset() {{
          const sd = root.api.superData;
          // 恢复静止坐标（基于 basePos）
          if (sd && sd.atomWorldPos && this.basePos) {{
            for (let i = 0; i < sd.atomWorldPos.length; i++) {{
              sd.atomWorldPos[i] = this.basePos[i];
            }}
          }}
          // 清空箭头
          const arrows = root.getObjectByName("arrows");
          if (arrows) {{
            root.remove(arrows);
          }}
          //console.log("reset() called, arrows.count =", arrows ? arrows.count : 0);
          // 清空轨迹
          if (this.ellipseTrajs) {{
            root.remove(this.ellipseTrajs);
            this.ellipseTrajs = null;
          }}
          this.showTrajs = false;
          // 清空选中的轨迹
          if (this.selectedAtoms && this.selectedAtoms.length > 0) {{
            this.selectedAtoms.forEach(id => {{
              const obj = root.getObjectByName(`ellipse_${{id}}`);
              if (obj) root.remove(obj);
            }});
            this.selectedAtoms = [];
          }}
          // 更新原子和键
          updateInstancedAtoms(root);
          updateInstancedBonds(root);
          // 清空声子数据
          this.modeDispR = null; 
          this.modeDispI = null; 
          this.instDispR = null;
          this.instDispI = null;
          this.instPhase = null;
          this.omega = 0;
        }}  
      }};
      //暴露自动旋转功能接口
      root.api.rotation = {{
        auto: false,
        toggle() {{
          this.auto = !this.auto;
          root.api.controls.autoRotate = this.auto;
          root.api.controls.autoRotateSpeed = 2.0;
        }},
        stop() {{
          this.auto = false;
          root.api.controls.autoRotate = false;
        }}
      }};

      // ===============================
      // 11. 渲染函数
      // ===============================
      //主渲染函数（核心）
      function renderSupercell(nx, ny, nz) {{
        // 只更新 supercell 数据，不渲染
        const superData = buildSupercore(data, nx, ny, nz);
        root.api.superData = superData;
      }};

      // ===============================
      // 12. 模式功能显示器
      // ===============================
      // ① 球 / 棍 / 球棍切换
      function applyModelStyle() {{
        const style = root.state.modelStyle;
        const atoms = root.getObjectByName("atoms");
        const bonds = root.getObjectByName("bonds");
        if (!atoms || !bonds) return;
        if (style === "sphere") {{
          atoms.visible = true;
          bonds.visible = false;

          const dummy = new THREE.Object3D();
          const scaleFactor = 2.5;  // 缩放系数，还原默认共价半径
          for (let i = 0; i < atoms.count; i++) {{
            atoms.getMatrixAt(i, dummy.matrix);
            dummy.matrix.decompose(dummy.position, dummy.quaternion, dummy.scale);
            // 在原有半径基础上放大
            dummy.scale.multiplyScalar(scaleFactor);
            dummy.updateMatrix();
            atoms.setMatrixAt(i, dummy.matrix);
          }}
          atoms.instanceMatrix.needsUpdate = true;
        }} else if (style === "stick") {{
          atoms.visible = false;
          bonds.visible = true;
        }} else {{ // "ballstick"
          atoms.visible = true;
          bonds.visible = true;
        }}
      }};
      // ② 生成多面体
      //生成多面体集
      function getMergedPolyhedra(mergedData) {{
        const A = mergedData.cell;
        const P = mergedData.positions;
        const frac = mergedData.scaled_positions;
        const adj = buildAdjacencyList(mergedData);

        const polyhedra = [];
        const N = mergedData.natoms;

        for (let i = 0; i < N; i++) {{
          if (mergedData.charges[i] <= 0) continue; // 中心原子

          const cx = P[i][0], cy = P[i][1], cz = P[i][2];
          const center = new THREE.Vector3(cx, cy, cz);
          const vertices = [];

          for (const nb of adj[i]) {{
            const j = nb.j;
            if (mergedData.charges[j] >= 0) continue;

            const fr = frac[j];

            const vx =
              (fr[0] + nb.offset[0]) * A[0][0] +
              (fr[1] + nb.offset[1]) * A[1][0] +
              (fr[2] + nb.offset[2]) * A[2][0];
            const vy =
              (fr[0] + nb.offset[0]) * A[0][1] +
              (fr[1] + nb.offset[1]) * A[1][1] +
              (fr[2] + nb.offset[2]) * A[2][1];
            const vz =
              (fr[0] + nb.offset[0]) * A[0][2] +
              (fr[1] + nb.offset[1]) * A[1][2] +
              (fr[2] + nb.offset[2]) * A[2][2];

            vertices.push(new THREE.Vector3(
              vx - cx,
              vy - cy,
              vz - cz
            ));
          }}

          if (vertices.length >= 3) {{
            polyhedra.push({{
              centerIndex: i,
              center,
              vertices
            }});
          }}
        }}

        return polyhedra;
      }}
      // 构建模板几何体
      function buildPolyhedronTemplates(polyhedra) {{
        const geomMap = new Map();

        for (const poly of polyhedra) {{
          const geom = new ConvexGeometry(poly.vertices);
          const edges = new THREE.EdgesGeometry(geom);
          geomMap.set(poly.centerIndex, {{ geom, edges }});
        }}

        return geomMap;
      }}
      // 平移复制 + map 去重
      function buildPolyhedraInstances(superData, mergedPolyhedra) {{
        const {{ baseIndex, atomWorldPos }} = superData;
        const instances = [];
        const seen = new Set();

        const polyMap = new Map();
        for (const poly of mergedPolyhedra) {{
          polyMap.set(poly.centerIndex, poly);
        }}

        const total = baseIndex.length;

        for (let inst = 0; inst < total; inst++) {{
          const base = baseIndex[inst];

          if (!polyMap.has(base)) continue;

          const poly = polyMap.get(base);

          const cx = atomWorldPos[inst*3];
          const cy = atomWorldPos[inst*3+1];
          const cz = atomWorldPos[inst*3+2];

          const worldCenter = new THREE.Vector3(cx, cy, cz);

          const key = `${{worldCenter.x.toFixed(6)}}_${{worldCenter.y.toFixed(6)}}_${{worldCenter.z.toFixed(6)}}`;
          if (seen.has(key)) continue;
          seen.add(key);

          instances.push({{
            poly,
            worldCenter
          }});
        }}

        return instances;
      }}
      // 渲染多面体
      function drawPolyhedraPolycentric() {{
        // 1. 清除旧多面体
        const old = root.getObjectByName("polyhedraGroup");
        if (old) root.remove(old);
        const group = new THREE.Group();
        group.name = "polyhedraGroup";
        // 2. supercell 数据
        const superData = root.api.superData;
        const mergedData = superData.data;
        // 3. 合胞多面体全集
        const mergedPolyhedra = getMergedPolyhedra(mergedData);
        // 4. 模板几何体
        const geomMap = buildPolyhedronTemplates(mergedPolyhedra);
        // 5. 超胞实例（平移 + 去重）
        const instances = buildPolyhedraInstances(superData, mergedPolyhedra);
        // 6. 渲染每个实例
        for (const inst of instances) {{
          const poly = inst.poly;
          const geomPack = geomMap.get(poly.centerIndex);
          if (!geomPack) continue;

          const {{ geom, edges }} = geomPack;

          const colorIndex = poly.centerIndex % mergedData.natoms;
          const hex = mergedData.colors[colorIndex];
          // ---------- 1. 深度遮罩层 ----------
          const depthPoly = new THREE.Mesh(geom, depthMaskMaterial);
          depthPoly.renderOrder = 0;
          // ---------- 2. 半透明外壳层 ----------
          const shellMat = polyMaterial.clone();
          shellMat.uniforms.uColor.value.set(hex);
          shellMat.transparent = true;
          shellMat.depthWrite = false;
          shellMat.depthTest = true;

          const shellPoly = new THREE.Mesh(geom, shellMat);
          shellPoly.renderOrder = 1;
          // ---------- 3. 边框线 ----------
          const line = new THREE.LineSegments(
            edges,
            new THREE.LineBasicMaterial({{
              color: new THREE.Color(hex).multiplyScalar(0.6)
            }})
          );
          line.renderOrder = 2;
          // ---------- 组合 ----------
          const g = new THREE.Group();
          g.add(depthPoly);
          g.add(shellPoly);
          g.add(line);
          // 正确的世界坐标：原胞中心 + 超胞偏移
          g.position.copy(inst.worldCenter);
          group.add(g);
        }}
        root.add(group);
      }}
        
      // ===============================
      // 13. 渲染调度中心
      // ===============================
      root.updateScene = function() {{
        // 清空场景
        while (root.children.length > 0) {{
          root.remove(root.children[0]);
        }}
        // 获取扩胞参数
        const nx = root.state.nx;
        const ny = root.state.ny;
        const nz = root.state.nz;
        // 根据模式合并原胞 + 壳
        const superData = mergeSupercells(data, root.state, nx, ny, nz);
        root.api.superData = superData;
        // 渲染原子
        const atoms = renderAtomsInstanced(superData, superData.data);
        atoms.name = "atoms";
        root.add(atoms);
        // 渲染键
        const bonds = renderBondsInstanced(superData, superData.data);
        bonds.name = "bonds";
        root.add(bonds);
        // 渲染晶胞框
        root.add(createCellFrame(data.cell));
        // 渲染晶胞坐标轴
        root.add(createCrystalAxes(data.cell));
        // 应用模型样式（球/棍/球棍）
        applyModelStyle();
        // 绘制多面体
        if (root.state.showPolyhedron === true) {{
          drawPolyhedraPolycentric();
        }}
        // 更新晶胞轴
        updateCenter();
        root.api.a_axis = new THREE.Vector3(...data.cell[0]);
        root.api.b_axis = new THREE.Vector3(...data.cell[1]);
        root.api.c_axis = new THREE.Vector3(...data.cell[2]);
        // 更新声子取向箭头
        const ph = root.api.phonon;
        // 扩胞后重新初始化声子模式
        if (ph.enabled && ph.modeIndex != null) {{
          initPhononMode(ph.modeIndex);
        }}
        if (ph.enabled && root.state.cellMode === "primitive" && ph.modeDispR && ph.instDispI) {{
          // basePos 与 superData 对齐
          ph.basePos = new Float32Array(superData.atomWorldPos);
          // 创建静态箭头
          const arrows = renderArrowsInstanced(ph.basePos, ph.instDispR, ph.instDispI, ph.amplitude);
          arrows.name = "arrows";
          //console.log("arrow mesh added to scene:", arrows);
          root.add(arrows);
        }}
        if (ph.enabled && ph.showTrajs) {{
          if (ph.ellipseTrajs) {{
            root.remove(ph.ellipseTrajs);
          }}
          // 创建静态轨迹
          ph.ellipseTrajs = renderEllipseTrajectories(ph.basePos, ph.instDispR, ph.instDispI, ph.amplitude);
          ph.ellipseTrajs.name = "ellipseTrajs";
          root.add(ph.ellipseTrajs);
        }}
        //console.log("updateScene: ph.enabled =", ph.enabled, "basePos =", ph.basePos);
      }};
      // ===============================
      // 14. UI 事件（扩胞）
      // ===============================
      // 初始扩胞
      root.api.setSupercell(1, 1, 1);
      // 初始晶胞交互
      setupPicking(renderer, camera, scene, data)
      // ===============================
      // 15. 声子动画
      // ===============================
      // buildModeDisplacement()——解析当前声子模式
      function buildModeDisplacement(band) {{
        const eig = band.eigenvector;
        const N = eig.length;
        const dispR = new Float32Array(N * 3);    // 实部数组
        const dispI = new Float32Array(N * 3);    // 虚部数组
        for (let i = 0; i < N; i++) {{
          dispR[i*3]   = eig[i][0][0];    // 实部x
          dispR[i*3+1] = eig[i][1][0];    // 实部y
          dispR[i*3+2] = eig[i][2][0];    // 实部z
          dispI[i*3]   = eig[i][0][1];    // 虚部i
          dispI[i*3+1] = eig[i][1][1];    // 虚部j
          dispI[i*3+2] = eig[i][2][1];    // 虚部k
        }}
        return {{ dispR, dispI }};
      }}
      // buildInstanceDisplacement()——解析当前声子扩展到超胞尺寸
      function buildInstanceDisplacement(superData, modeDisp) {{
        const {{ baseIndex }} = superData;
        const M = baseIndex.length;
        const instDisp = new Float32Array(M * 3);

        for (let inst = 0; inst < M; inst++) {{
          const base = baseIndex[inst];
          instDisp[inst*3]   = modeDisp[base*3];
          instDisp[inst*3+1] = modeDisp[base*3+1];
          instDisp[inst*3+2] = modeDisp[base*3+2];
        }}
        return instDisp;
      }}
      // initPhononMode()——初始化声子模式
      function initPhononMode(modeIndex) {{
        const ph = root.api.phonon;
        //console.log("initPhononMode called, modeIndex =", modeIndex);
        if (root.state.cellMode !== "primitive") {{
          //console.log("initPhononMode: cellMode is", root.state.cellMode, "→ abort");
          ph.modeDispR = null;
          ph.modeDispI = null;
          ph.instDispR = null;
          ph.instDispI = null;
          ph.instPhase = null;
          ph.omega = 0;
          return;
        }}
        const band = phononData.band[modeIndex];
        const {{ dispR, dispI }} = buildModeDisplacement(band);
        // 1. 本征向量实部及扩胞
        ph.modeDispR = dispR;
        ph.instDispR = buildInstanceDisplacement(root.api.superData, dispR);
        //console.log("modeDisp length =", ph.modeDisp.length, "sample =", ph.modeDisp[0], ph.modeDisp[1], ph.modeDisp[2]);
        // 2. 本征向量虚部及扩胞
        ph.modeDispI = dispI;
        ph.instDispI = buildInstanceDisplacement(root.api.superData, dispI);
        // 3. 相位数组
        ph.instPhase = new Float32Array(root.api.superData.baseIndex.length);
        // 4. 角频率 = 用户指定频率（Hz）× 2π
        ph.omega = 2 * Math.PI * ph.frequencyScale;
      }}
      // buildArrowRenderInfo()——转译本征向量
      function buildArrowRenderInfo(basePos, instDispR, instDispI, amplitude) {{
        const M = basePos.length / 3;

        const matricesShaft = new Array(M);
        const matricesHead  = new Array(M);

        const dummy = new THREE.Object3D();
        const yAxis = new THREE.Vector3(0, 1, 0);

        for (let inst = 0; inst < M; inst++) {{
          // 原子位置
          const ax = basePos[inst*3];
          const ay = basePos[inst*3+1];
          const az = basePos[inst*3+2];
          const atomPos = new THREE.Vector3(ax, ay, az);
          // 实部
          const dxR = instDispR[inst*3];
          const dyR = instDispR[inst*3+1];
          const dzR = instDispR[inst*3+2];
          // 虚部
          const dxI = instDispI[inst*3];
          const dyI = instDispI[inst*3+1];
          const dzI = instDispI[inst*3+2];
          const eigenLen = Math.sqrt(dxR*dxR + dyR*dyR + dzR*dzR + dxI*dxI + dyI*dyI + dzI*dzI);
          if (eigenLen < 1e-12) {{
            dummy.position.copy(atomPos);
            dummy.scale.set(1, 0.0001, 1);
            dummy.updateMatrix();
            matricesShaft[inst] = dummy.matrix.clone();
            matricesHead[inst]  = dummy.matrix.clone();
            continue;
          }}
          const dir = new THREE.Vector3(dxR+dxI, dyR+dyI, dzR+dzI).normalize();
          const len = eigenLen * amplitude;
          // shaft
          dummy.position.copy(atomPos);
          dummy.quaternion.setFromUnitVectors(yAxis, dir);
          dummy.scale.set(1, len, 1);
          dummy.updateMatrix();
          matricesShaft[inst] = dummy.matrix.clone();
          // head
          dummy.position.copy(atomPos).addScaledVector(dir, len);
          dummy.quaternion.setFromUnitVectors(yAxis, dir);
          dummy.scale.set(1, 1, 1);
          dummy.updateMatrix();
          matricesHead[inst] = dummy.matrix.clone();
        }}
        return {{ matricesShaft, matricesHead }};
      }}
      // buildEllipseCurve()——计算声子运动轨迹
      function buildEllipseCurve(atomPos, dxR, dyR, dzR, dxI, dyI, dzI, amplitude, segments = 64) {{
        const points = [];
        for (let i = 0; i <= segments; i++) {{
          const phi = (i / segments) * 2 * Math.PI;
          const c = Math.cos(phi);
          const s = Math.sin(phi);

          const ux = (dxR * c - dxI * s) * amplitude;
          const uy = (dyR * c - dyI * s) * amplitude;
          const uz = (dzR * c - dzI * s) * amplitude;

          points.push(new THREE.Vector3(atomPos.x + ux, atomPos.y + uy, atomPos.z + uz));
        }}
        return new THREE.BufferGeometry().setFromPoints(points);
      }}
      // renderArrowsInstanced()——渲染本征向量为箭头
      function renderArrowsInstanced(basePos, instDispR, instDispI, amplitude) {{
        // 创建箭头模型
        function buildArrowGeometry() {{
          const shaftHeight = 1.0;
          const shaftRadius = 0.05;

          const headHeight = 0.3;
          const headRadius = 0.12;
          // 箭杆（Cylinder）
          const shaftGeo = new THREE.CylinderGeometry(
            shaftRadius, shaftRadius,
            shaftHeight,
            16, 1, true
          );
          shaftGeo.translate(0, shaftHeight/2, 0);  // 底部对齐 y=0
          // 箭头头部（Cone）
          const headGeo = new THREE.ConeGeometry(
            headRadius,
            headHeight,
            16
          );
          headGeo.translate(0, 0, 0); // 底部对齐到箭杆顶部

          return {{ shaftGeo, headGeo }};
        }}
        const {{ matricesShaft, matricesHead }} =
          buildArrowRenderInfo(basePos, instDispR, instDispI, amplitude);

        const {{ shaftGeo, headGeo }} = buildArrowGeometry();

        const meshShaft = buildInstancedMesh(shaftGeo, arrowMaterial, matricesShaft);
        const meshHead  = buildInstancedMesh(headGeo,  arrowMaterial, matricesHead);

        const group = new THREE.Group();
        group.add(meshShaft);
        group.add(meshHead);
        group.name = "arrows";

        return group;
      }}
      // renderEllipseTrajectories()——渲染声子运动椭圆轨迹
      function renderEllipseTrajectories(basePos, instDispR, instDispI, amplitude,  targetIndex = null) {{
        const group = new THREE.Group();
        const M = basePos.length / 3;

        for (let inst = 0; inst < M; inst++) {{
          // 如果指定了 targetIndex，则跳过其他原子
          if (targetIndex !== null && inst !== targetIndex) continue;

          const ax = basePos[inst*3];
          const ay = basePos[inst*3+1];
          const az = basePos[inst*3+2];
          const atomPos = new THREE.Vector3(ax, ay, az);

          const dxR = instDispR[inst*3];
          const dyR = instDispR[inst*3+1];
          const dzR = instDispR[inst*3+2];

          const dxI = instDispI[inst*3];
          const dyI = instDispI[inst*3+1];
          const dzI = instDispI[inst*3+2];

          const geo = buildEllipseCurve(atomPos, dxR, dyR, dzR, dxI, dyI, dzI, amplitude);

          const mat = new THREE.LineBasicMaterial({{
            color: 0xffaa00,
            transparent: true,
            opacity: 0.8
          }});

          const line = new THREE.Line(geo, mat);
          group.add(line);
        }}

        group.name = "ellipseTrajs";
        return group;
      }}
      // updatePhononFrameUnified()——声子运动方程
      function updatePhononFrameUnified(t, superData, instDispR ,instDispI , instPhase, omega, basePos, amplitude) {{
        if (!instDispR || !instDispI || !instPhase || !omega || !basePos) return;

        const {{ atomWorldPos }} = superData;
        const M = atomWorldPos.length / 3;
        // 恢复静止坐标
        for (let i = 0; i < atomWorldPos.length; i++) {{
          atomWorldPos[i] = basePos[i];
        }}
        // 叠加复数振动位移
        for (let inst = 0; inst < M; inst++) {{
          const phase = omega * t - instPhase[inst];
          const c = Math.cos(phase);
          const s = Math.sin(phase);
          // u = eR * cos - eI * sin
          atomWorldPos[inst*3]     += (instDispR[inst*3]     * c - instDispI[inst*3]     * s) * amplitude;
          atomWorldPos[inst*3 + 1] += (instDispR[inst*3 + 1] * c - instDispI[inst*3 + 1] * s) * amplitude;
          atomWorldPos[inst*3 + 2] += (instDispR[inst*3 + 2] * c - instDispI[inst*3 + 2] * s) * amplitude;
        }}
      }}
      // updateInstancedAtoms()——更新原子位置
      function updateInstancedAtoms(root) {{
        const atoms = root.getObjectByName("atoms");
        if (!atoms) return;
       
        const {{ matrices }} = buildAtomRenderInfo(root.api.superData, root.api.superData.data);

        for (let i = 0; i < matrices.length; i++) {{
          atoms.setMatrixAt(i, matrices[i]);
        }}
        atoms.instanceMatrix.needsUpdate = true;
      }}
      // updateInstancedBonds()——更新化学键位置
      function updateInstancedBonds(root) {{
        const bondsGroup = root.getObjectByName("bonds");
        if (!bondsGroup) return;

        const info = buildBondRenderInfo(root.api.superData, root.api.superData.data);

        const cyl  = bondsGroup.getObjectByName("bonds_cyl");
        const sphA = bondsGroup.getObjectByName("bonds_sphereA");
        const sphB = bondsGroup.getObjectByName("bonds_sphereB");

        info.matrices.forEach((m, i)  => cyl.setMatrixAt(i, m));
        info.matricesA.forEach((m, i) => sphA.setMatrixAt(i, m));
        info.matricesB.forEach((m, i) => sphB.setMatrixAt(i, m));

        cyl.instanceMatrix.needsUpdate  = true;
        sphA.instanceMatrix.needsUpdate = true;
        sphB.instanceMatrix.needsUpdate = true;
      }}
      // updateInstancedArrows()——更新本征向量箭头位置、长度、取向
      function updateInstancedArrows(arrows, superData, instDispR, instDispI, instPhase, omega, t, amplitude, basePos) {{
        if (!arrows) return;
        const shaft = arrows.children[0]; // InstancedMesh（箭杆）
        const head  = arrows.children[1]; // InstancedMesh（箭头）
        const atomPos = superData.atomWorldPos; // 振动后的原子位置
        const dummy = new THREE.Object3D();
        const M = instDispR.length / 3;
        const yAxis = new THREE.Vector3(0, 1, 0);
        for (let inst = 0; inst < M; inst++) {{
          // 1. 原子当前位置（箭尾）
          const ax = atomPos[inst*3];
          const ay = atomPos[inst*3+1];
          const az = atomPos[inst*3+2];
          const tail = new THREE.Vector3(ax, ay, az);
          // 2. 相位
          const phase = omega * t - instPhase[inst];
          const c = Math.cos(phase);
          const s = Math.sin(phase);
          // 3. 实部
          const dxR = instDispR[inst*3];
          const dyR = instDispR[inst*3+1];
          const dzR = instDispR[inst*3+2];
          // 4. 虚部
          const dxI = instDispI[inst*3];
          const dyI = instDispI[inst*3+1];
          const dzI = instDispI[inst*3+2];
          // 4. 方向 = 极化方向 p(t)
          const px = dxR * c - dxI * s;
          const py = dyR * c - dyI * s;
          const pz = dzR * c - dzI * s;
          const dir = new THREE.Vector3(px, py, pz).normalize();
          // 5. 长度 = |u(t)|
          const ux = (dxR * c - dxI * s) * amplitude;
          const uy = (dyR * c - dyI * s) * amplitude;
          const uz = (dzR * c - dzI * s) * amplitude;
          const len = Math.sqrt(ux*ux + uy*uy + uz*uz);
          if (len < 1e-12) {{
            // 本征向量为 0 → 箭头缩成 0
            dummy.position.copy(tail);
            dummy.scale.set(1, 0.0001, 1);
            dummy.quaternion.identity();
            dummy.updateMatrix();
            shaft.setMatrixAt(inst, dummy.matrix);
            head.setMatrixAt(inst, dummy.matrix);
            continue;
          }}
          // 6. 更新箭杆
          dummy.position.copy(tail);
          dummy.quaternion.setFromUnitVectors(yAxis, dir);
          dummy.scale.set(1, len, 1);
          dummy.updateMatrix();
          shaft.setMatrixAt(inst, dummy.matrix);
          // 7. 更新箭头头
          dummy.position.copy(tail).addScaledVector(dir, len);
          dummy.quaternion.setFromUnitVectors(yAxis, dir);
          dummy.scale.set(1, 1, 1);
          dummy.updateMatrix();
          head.setMatrixAt(inst, dummy.matrix);
        }}
        shaft.instanceMatrix.needsUpdate = true;
        head.instanceMatrix.needsUpdate = true;
      }}
      
      // ===============================
      // 16. 动画循环
      // ===============================
      function animate(time) {{
        requestAnimationFrame(animate);
        controls.update();
        const ph = root.api.phonon;
        if (ph.enabled && root.state.cellMode === "primitive") {{
          const t = time * 0.001;
          const arrows = root.getObjectByName("arrows");
          // 播放时更新原子位置
          if (ph.playing && arrows) {{
            updatePhononFrameUnified(
              t,
              root.api.superData,
              ph.instDispR,
              ph.instDispI,
              ph.instPhase,
              ph.omega,
              ph.basePos,
              ph.amplitude
            );
            updateInstancedAtoms(root);
            updateInstancedBonds(root);
            updateInstancedArrows(
              arrows,
              root.api.superData,
              ph.instDispR,
              ph.instDispI,
              ph.instPhase,
              ph.omega,
              t,
              ph.amplitude,
              ph.basePos
            );
          }}
        }}
        // 结构渲染
        renderer.render(scene, camera);
      }}
      animate();
    </script>
    <div id="legend-box">    </div>
    <script>
      // 自动生成图例
      function createLegend(data) {{
        const legendBox = document.getElementById("legend-box");
        legendBox.innerHTML = "";

        const unique = [];
        data.symbols.forEach((sym, i) => {{
          if (!unique.find(e => e.symbol === sym)) {{
            unique.push({{ symbol: sym, color: data.colors[i] }});
          }}
        }});

        unique.forEach(e => {{
          const item = document.createElement("div");
          item.className = "legend-item";

          const dot = document.createElement("span");
          dot.className = "legend-color";
          dot.style.background = e.color;

          item.appendChild(dot);
          item.appendChild(document.createTextNode(e.symbol));
          legendBox.appendChild(item);
        }});
      }}
    </script>
  </div>
"""
    return js_renderer

# htmlUI控件块生成器
def js_ui(phonondata):
    # 当未传入声子数据时不载入声子相关UI控件
    if phonondata is None:
        phonon_bar = f""""""
    # 否则载入声子相关UI控件
    else:
        phonon_bar = f"""
    <!-- 声子 -->
    <div class="phonon-bar">
      <button class="phonon-btn">声子</button>
      <label>频率</label>
      <input type="number" id="Frequency" max="10.0" value="0.5" min="0.1" step="0.1">
      <label>增幅</label>
      <input type="number" id="Amplitude" max="10.0" value="5.0" min="0.0" step="0.5">
    </div>
    <div class="phonon-bar">
      <button class="phonon-btn">旋转</button>
      <button class="phonon-btn">播放</button>
      <button class="phonon-btn">轨迹</button>
    </div>
    <script>
      document.addEventListener("root-ready", (e) => {{
        const root = e.detail.root;
        const ph = root.api.phonon;
        const rot = root.api.rotation;
        // === 1. 获取 UI 控件 ===
        const btnPhonon = document.querySelectorAll(".phonon-btn")[0];    // 声子
        const btnRotate = document.querySelectorAll(".phonon-btn")[1];    // 旋转
        const btnPlay   = document.querySelectorAll(".phonon-btn")[2];    // 播放
        const btnTrajs  = document.querySelectorAll(".phonon-btn")[3];    // 轨迹
        const inputFreq = document.getElementById("Frequency");    // 频率
        const inputAmp  = document.getElementById("Amplitude");    // 增幅
        // === 2. 初始全部禁用 ===
        disableControls();
        // 关闭声子展示控制台
        function disableControls() {{
          btnRotate.disabled = true;
          btnPlay.disabled = true;
          btnTrajs.disabled = true;
          inputFreq.disabled = true;
          inputAmp.disabled = true;
          btnRotate.style.opacity = 0.5;
          btnPlay.style.opacity = 0.5;
          btnTrajs.style.opacity = 0.5;
          inputFreq.style.opacity = 0.5;
          inputAmp.style.opacity = 0.5;
        }}
        // 开启声子展示控制台
        function enableControls() {{
          btnRotate.disabled = false;
          btnPlay.disabled = false;
          btnTrajs.disabled = false;
          inputFreq.disabled = false;
          inputAmp.disabled = false;
          btnRotate.style.opacity = 1.0;
          btnPlay.style.opacity = 1.0;
          btnTrajs.style.opacity = 1.0;
          inputFreq.style.opacity = 1.0;
          inputAmp.style.opacity = 1.0;
        }}
        // === 3. 声子按钮：开启/关闭声子模式 ===
        btnPhonon.addEventListener("click", () => {{
          if (!ph.enabled) {{
            // 开启声子模式
            ph.enable();
            btnPhonon.classList.add("active");   // 声子按钮加 active
            root.updateScene(); 
            enableControls(); // ← 关键：启用所有控件

            btnPlay.textContent = "播放";
            btnRotate.textContent = "旋转";

            console.log("声子模式已开启");
          }} else {{
            // 关闭声子模式
            ph.disable();
            btnPhonon.classList.remove("active"); // 声子按钮移除 active
            btnTrajs.classList.remove("active"); // 复位轨迹按钮移除 active
            root.updateScene(); 
            disableControls(); // ← 关键：禁用所有控件

            btnPlay.textContent = "播放";
            btnRotate.textContent = "旋转";

            console.log("声子模式已关闭");
          }}
        }});
        // === 4. 频率控制 ===
        inputFreq.addEventListener("input", () => {{
          ph.setFrequencyScale(parseFloat(inputFreq.value));
        }});
        // === 5. 增幅控制 ===
        inputAmp.addEventListener("input", () => {{
          ph.setAmplitude(parseFloat(inputAmp.value));
          root.updateScene(); 
        }});
        // === 6. 播放按钮 ===
        btnPlay.addEventListener("click", () => {{
          if (!ph.enabled) return;

          ph.togglePlay();
          btnPlay.textContent = ph.playing ? "暂停" : "播放";
        }});
        // === 7. 旋转按钮 ===
        btnRotate.addEventListener("click", () => {{
          rot.toggle();
          btnRotate.textContent = rot.auto ? "停止" : "旋转";
        }});
        // === 8. 轨迹按钮 ===
        btnTrajs.addEventListener("click", () => {{
          ph.toggleEllipse();
          // 根据状态切换 active 样式
          if (ph.showTrajs) {{
            btnTrajs.classList.add("active");
            console.log("声子轨迹已显示");
          }} else {{
            btnTrajs.classList.remove("active");
            console.log("声子轨迹已关闭");
          }}
        }});
      }});
    </script>
"""
    # 主UI控件
    js_ui = f"""
  <div id="controls">
    <!-- 单胞 / 常规晶胞 -->
    <div id="cellmode-container">
      <div class="cellmode-btn " data-mode="primitive">原胞</div>
      <div class="cellmode-btn active" data-mode="conventional">常规胞</div>
    </div>
    <!-- 晶体学 / 配位化学 -->
    <div id="chemistry-mode">
      <div class="chem-btn " data-type="crystal">
        <input type="checkbox" id="crystal-checkbox" checked>
        <span>晶体学</span>
      </div>
      <div class="chem-btn " data-type="coordination">
        <input type="checkbox" id="coordination-checkbox" >
        <span>配位化学</span>
      </div>
    </div>
    <!-- 模型样式 -->
    <div class="section-box">
      <div class="section-title">模型样式</div>
      <label><input type="radio" name="model" value="sphere"> 球</label><br>
      <label><input type="radio" name="model" value="stick"> 棍</label><br>
      <label><input type="radio" name="model" value="ballstick" checked> 球棍</label><br>
      <label><input type="checkbox" id="polyhedron"> 配位多面体</label>
    </div>
    <script>
      updataHeader(data)
      createLegend(data)
      document.querySelectorAll(".cellmode-btn").forEach(btn => {{
        btn.addEventListener("click", () => {{
          classMode = btn.dataset.mode;   // 修改全局 mode
          data = rawData[classMode]
          updataHeader(data);            // 更新 header
          createLegend(data)
        }});
      }});
      document.addEventListener("root-ready", (e) => {{
        const root = e.detail.root;
        // --- 获取元素 ---
        const cellBtns = document.querySelectorAll(".cellmode-btn");
        const chemBtns = document.querySelectorAll(".chem-btn");
        const crystal = document.getElementById("crystal-checkbox");
        const coordination = document.getElementById("coordination-checkbox");

        const modelRadios = document.querySelectorAll("input[name='model']");
        const polyhedron = document.getElementById("polyhedron");

        const expandX = document.getElementById("expandX");
        const expandY = document.getElementById("expandY");
        const expandZ = document.getElementById("expandZ");
        // ============================
        // 工具函数：检查条件并自动取消配位多面体
        // ============================
        function validatePolyhedron() {{
          const isConventional =
            document.querySelector(".cellmode-btn.active").dataset.mode === "conventional";
          const isCoordination = coordination.checked;
          const isBallStick =
            document.querySelector("input[name='model']:checked")?.value === "ballstick";

          const ok = isConventional && isCoordination && isBallStick;

          if (!ok) {{
            polyhedron.checked = false;
            root.api.togglePolyhedron(false);
          }}
        }}
        // ============================
        // 单胞 / 常规晶胞切换
        // ============================
        cellBtns.forEach(btn => {{
          btn.addEventListener("click", () => {{

            // 互斥切换 active
            cellBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");

            const mode = btn.dataset.mode;

            // 调用 root.api
            root.api.setCellMode(mode);

            if (mode === "primitive") {{
              // 单胞 → 禁用晶体学/配位化学
              chemBtns.forEach(c => c.classList.add("disabled"));
              crystal.disabled = true;
              coordination.disabled = true;
              crystal.checked = false;
              coordination.checked = false;
              expandX.disabled = false;
              expandY.disabled = false;
              expandZ.disabled = false;
              // 强制回到 1×1×1
              expandX.value = 1;
              expandY.value = 1;
              expandZ.value = 1;
              // 通知渲染器复位单胞
              root.api.setSupercell(1, 1, 1);
            }} else {{
              // 常规晶胞 → 启用晶体学/配位化学
              chemBtns.forEach(c => c.classList.remove("disabled"));
              crystal.disabled = false;
              coordination.disabled = false;
              crystal.checked = true;
              coordination.checked = false;
              expandX.disabled = false;
              expandY.disabled = false;
              expandZ.disabled = false;
              // 强制回到 1×1×1
              expandX.value = 1;
              expandY.value = 1;
              expandZ.value = 1;
              // 通知渲染器复位单胞
              root.api.setSupercell(1, 1, 1);
              // 开启晶体学模式
              root.api.setChemistryMode("crystal");
            }}
            validatePolyhedron();
          }});
        }});
        //============================
        // 晶体学 / 配位化学 二选一
        // ============================
        crystal.addEventListener("change", () => {{
          if (crystal.checked) {{
            polyhedron.checked = false;
            root.state.showPolyhedron = false;
            coordination.checked = false;
            root.api.setChemistryMode("crystal");
          }}
          validatePolyhedron();
        }});
        coordination.addEventListener("change", () => {{
          if (coordination.checked) {{
            crystal.checked = false;
            root.api.setChemistryMode("coordination");
          }}
          validatePolyhedron();
        }});
        // ============================
        // 模型样式（球/棍/球棍）
        // ============================
        modelRadios.forEach(r => {{
          r.addEventListener("change", () => {{
            root.api.setModelStyle(r.value);
            validatePolyhedron();
          }});
        }});
        // ============================
        // 反向逻辑：点击配位多面体时强制满足条件
        // ============================
        polyhedron.addEventListener("change", () => {{
          if (polyhedron.checked) {{
            // 1. 切换到常规晶胞UI
            document.querySelector(".cellmode-btn[data-mode='primitive']").classList.remove("active");
            document.querySelector(".cellmode-btn[data-mode='conventional']").classList.add("active");
            if (classMode ==="primitive"){{
              classMode = "conventional";   // 修改全局 mode
              data = rawData[classMode]
              updataHeader(data);            // 更新 header
              createLegend(data);
              // 强制回到 1×1×1
              expandX.value = 1;
              expandY.value = 1;
              expandZ.value = 1;
              // 通知渲染器复位单胞
              root.api.setSupercell(1, 1, 1);
          }}
            // 2. 一次性更新所有渲染状态
            root.state.cellMode = "conventional";   // 切换到常规晶胞
            root.state.chemistryMode = "coordination";    // 切换到配位化学模式
            root.state.modelStyle = "ballstick";   // 切换到球棍模型
            root.state.showPolyhedron = true;    // 切换到配位多面体模式
            // 2. UI 同步
            chemBtns.forEach(c => c.classList.remove("disabled"));
            crystal.disabled = false;
            coordination.disabled = false;
            coordination.checked = true;
            crystal.checked = false;
            document.querySelector("input[name='model'][value='ballstick']").checked = true;
            // 4. 关键：恢复扩胞输入框
            expandX.disabled = false;
            expandY.disabled = false;
            expandZ.disabled = false;
            // 5. 恢复扩胞
            root.api.setSupercell(
              parseInt(expandX.value),
              parseInt(expandY.value),
              parseInt(expandZ.value)
            );
          }} else {{
            // 关闭多面体
            root.state.showPolyhedron = false;
            root.api.updateScene();
          }};
        }});
      }});
    </script>
    <!-- 旋转控制 -->
    <h3>旋转控制</h3>
    <!-- 刻度条 -->
    <div class="rotate-scale">
      <span> </span>
      <span>-180°</span>
      <span>-90°</span>
      <span>0°</span>
      <span>90°</span>
      <span>180°</span>
      <span> </span>
    </div>
    <!-- 三个滑块 + 显示值 -->
    <div class="rotate-row">
      <button id="btnA">a-axis</button>
      <input type="range" id="rotateA" min="-180" max="180" step="15">
      <span id="rotateA_val">0°</span>
    </div>
    <div class="rotate-row">
      <button id="btnB">b-axis</button>
      <input type="range" id="rotateB" min="-180" max="180" step="15">
      <span id="rotateB_val">0°</span>
    </div>
    <div class="rotate-row">
      <button id="btnC">c-axis</button>
      <input type="range" id="rotateC" min="-180" max="180" step="15">
      <span id="rotateC_val">0°</span>
    </div>
    <script>
      document.addEventListener("root-ready", (e) => {{
        const root = e.detail.root;
        const THREE = root.api.THREE;

        // === 1. 获取滑块 ===
        const rotateA = document.getElementById("rotateA");
        const rotateB = document.getElementById("rotateB");
        const rotateC = document.getElementById("rotateC");

        const rotateA_val = document.getElementById("rotateA_val");
        const rotateB_val = document.getElementById("rotateB_val");
        const rotateC_val = document.getElementById("rotateC_val");

        let angleA = 0, angleB = 0, angleC = 0;

        // === 2. 滑块旋转模型（保留你的功能） ===
        rotateA.addEventListener("input", () => {{
          angleA = THREE.MathUtils.degToRad(rotateA.value);
          rotateA_val.textContent = rotateA.value + "°";
          root.api.setRotation(angleA, angleB, angleC);
        }});

        rotateB.addEventListener("input", () => {{
          angleB = THREE.MathUtils.degToRad(rotateB.value);
          rotateB_val.textContent = rotateB.value + "°";
          root.api.setRotation(angleA, angleB, angleC);
        }});

        rotateC.addEventListener("input", () => {{
          angleC = THREE.MathUtils.degToRad(rotateC.value);
          rotateC_val.textContent = rotateC.value + "°";
          root.api.setRotation(angleA, angleB, angleC);
        }});

        // === 3. 视角对准晶胞轴 ===
        const a = root.api.a_axis;
        const b = root.api.b_axis;
        const c = root.api.c_axis;

        const camera = root.api.camera;
        const controls = root.api.controls;
        const center = root.api.center;

        function lookAlongAxis(axisVec) {{
          const dir = axisVec.clone().normalize();
          const distance = 80;  // 相机距离，可调
          const pos = center.clone().add(dir.multiplyScalar(distance));

          camera.position.copy(pos);
          camera.lookAt(center);

          controls.target.copy(center);
          controls.update();
        }}

        // === 4. 重置滑块 + 重置模型旋转 ===
        function resetSliders() {{
          rotateA.value = 0;
          rotateB.value = 0;
          rotateC.value = 0;

          rotateA_val.textContent = "0°";
          rotateB_val.textContent = "0°";
          rotateC_val.textContent = "0°";

          angleA = angleB = angleC = 0;
          root.api.setRotation(0, 0, 0);
        }}

        // === 5. 按钮绑定 ===
        document.getElementById("btnA").addEventListener("click", () => {{
          lookAlongAxis(a);
          resetSliders();
        }});

        document.getElementById("btnB").addEventListener("click", () => {{
          lookAlongAxis(b);
          resetSliders();
        }});

        document.getElementById("btnC").addEventListener("click", () => {{
          lookAlongAxis(c);
          resetSliders();
        }});
      }});
    </script>
    <!-- 扩胞 -->
    <div class="expand-bar">
      扩胞：
      X <input type="number" id="expandX" value="1" min="1">
      Y <input type="number" id="expandY" value="1" min="1">
      Z <input type="number" id="expandZ" value="1" min="1">
    </div>
    <script>
      document.addEventListener("root-ready", (e) => {{
        const root = e.detail.root;

        const expandX = document.getElementById("expandX");
        const expandY = document.getElementById("expandY");
        const expandZ = document.getElementById("expandZ");

        // 扩胞输入
        function updateSupercell() {{
          root.api.setSupercell(
            parseInt(expandX.value),
            parseInt(expandY.value),
            parseInt(expandZ.value)
          );
        }}
        expandX.addEventListener("input", updateSupercell);
        expandY.addEventListener("input", updateSupercell);
        expandZ.addEventListener("input", updateSupercell);
      }});
    </script>
    {phonon_bar}
  </div>

  <div id="result-area">
    <details open>
      <summary style="cursor:pointer; font-weight:bold;">测量日志</summary>
      <div id="log-content">
        <div id="log-watermark">
          计算结果展示区
        </div>
      </div>
    </details>
    <script>
    document.addEventListener("root-ready", (e) => {{
      const root = e.detail.root;
      // 监听 appendResult 事件
      document.addEventListener("append-result", (ev) => {{
        const {{ msg, div }} = ev.detail;
        // 隐藏水印
        const watermark = document.getElementById("log-watermark");
        if (watermark) watermark.style.display = "none";
        // 外部控制样式
        div.classList.add("log-entry");    //为导入的 <div> 赋予样式 .log-entry
        // 根据 msg 内容自动为内容赋予样式
        if (msg.includes("键长")) div.classList.add("distance");    //如果 msg 包含“键长”，赋予样式 .distance
        if (msg.includes("键角")) div.classList.add("angle");    //如果 msg 包含“键角”，赋予样式 .angle
        if (msg.includes("二面角")) div.classList.add("dihedral");    //如果 msg 包含“二面角”，赋予样式 .dihedral
        // 外部控制动画
        div.style.opacity = 0;    //刚插入时透明度为 0
        setTimeout(() => div.style.opacity = 1, 10);    //10ms 后变成 1
        // 外部控制插入位置
        document.getElementById("log-content").appendChild(div);    //把日志条目插入到<div id="log-content"></div>位置
        // 外部控制自动滚动
        const area = document.getElementById("result-area");    //获取日志区域外层容器 <div id="result-area">
        area.scrollTop = area.scrollHeight;    //把滚动条移动到最底部
      }});
      console.log("日志系统已初始化");
    }});
  </script>
  </div>
"""
    
    return js_ui