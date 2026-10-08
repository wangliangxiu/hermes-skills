# Government propaganda video example

From a real session (2026-06-25): user wanted a 4K 党政政务汇报情景剧 (government work report drama) but settled for an animated HTML Canvas version.

## Requirements that shaped the example

- **Theme:** "倾心履职为民 助力乡村全面振兴" (Serve the people, help rural revitalization)
- **Format:** 政协农业农村委员会工作汇报剧 (CPPCC Agriculture Committee work report drama)
- **Characters:** 女主持人 (host), 王主任 (director Wang), 2 政协委员 (CPPCC members), 农业专家 (agriculture expert), 农业局干部 (bureau cadre), 农技员 (agritech), 淳朴农户 (farmer)
- **Tone:** 沉稳青金政务色调 (solemn gold-and-navy government palette), 柔和演播厅灯光 (soft studio lighting), 管弦乐背景音乐 (orchestral background) — simulated as visual atmosphere
- **Duraton:** 2 min 30 sec (150 seconds)
- **Scenes:** Opening → 铸魂固本 → 靶向发力 → 品牌创建(五微协商) → 协同联动 → Ending
- **Subtitle:** Bottom bar, 黑体 (bold Chinese government font), formal tone
- **User rejection:** First attempt was CSS slides (翻页), user said "不是这种，是小视频，你这样搞得跟像是ppt了" — switched to Canvas animation

## Key code patterns from that session

### Canvas setup
```javascript
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const W = 1280, H = 720;
```

### Time-based rendering loop
```javascript
let t = 0; // global time in seconds
let playing = false;

function render(){
  // Clear
  ctx.fillStyle = DARK_BG;
  ctx.fillRect(0,0,W,H);
  
  // Background glow
  const pulse = 0.5+0.5*Math.sin(t*0.5);
  const grad = ctx.createRadialGradient(W/2, H*0.3, 0, W/2, H*0.3, 500);
  grad.addColorStop(0, `rgba(201,168,76,${0.02*pulse})`);
  grad.addColorStop(1, 'transparent');
  ctx.fillStyle = grad;
  ctx.fillRect(0,0,W,H);
  
  // Scene dispatch
  if(t<20) renderScene0(t);
  // ...
  
  if(playing) t += 1/60;
  requestAnimationFrame(render);
}
```

### Smooth element entrance (ease-in-out + slide up)
```javascript
function renderCard(ctx, x, y, icon, title, desc, localTime, delay){
  const appear = clamp((localTime - delay) / 0.6, 0, 1);
  const alpha = easeInOut(appear);
  if(alpha < 0.01) return;
  
  ctx.save();
  ctx.globalAlpha = alpha;
  const slideY = y + (1-alpha) * 30;
  
  // Card background
  ctx.fillStyle = 'rgba(255,255,255,0.03)';
  ctx.strokeStyle = `rgba(201,168,76,${0.12*alpha})`;
  roundRect(ctx, x, slideY, 220, 120, 6);
  ctx.fill(); ctx.stroke();
  
  // Card content
  ctx.font = '28px sans-serif';
  ctx.fillStyle = GOLD;
  ctx.textAlign = 'center';
  ctx.fillText(icon, x+110, slideY+40);
  ctx.font = 'bold 16px "Microsoft YaHei",sans-serif';
  ctx.fillStyle = GOLD;
  ctx.fillText(title, x+110, slideY+75);
  ctx.font = '13px "Microsoft YaHei",sans-serif';
  ctx.fillStyle = TEXT_LIGHT;
  ctx.fillText(desc, x+110, slideY+100);
  
  ctx.restore();
}
```

### Dialogue bubble with timed appearance
```javascript
const diagTime = localTime - 6; // start at 6s into the scene
if(diagTime > 0 && diagTime < 6){
  const da = clamp(diagTime/0.8, 0, 1);
  ctx.save();
  ctx.globalAlpha = easeInOut(Math.min(da, clamp((6-diagTime)/1.5, 0, 1)));
  ctx.font = '15px "Microsoft YaHei",sans-serif';
  ctx.fillStyle = TEXT_LIGHT;
  ctx.fillText('"dialogue text"', 185, 520);
  ctx.restore();
}
```

### Character avatar (circle + emoji)
```javascript
function drawAvatar(ctx, cx, cy, radius, emoji){
  ctx.beginPath();
  ctx.arc(cx, cy, radius, 0, Math.PI*2);
  ctx.fillStyle = '#1a3a5a';
  ctx.fill();
  ctx.strokeStyle = GOLD;
  ctx.lineWidth = 2;
  ctx.stroke();
  ctx.font = `${radius/2}px sans-serif`;
  ctx.fillStyle = GOLD;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(emoji, cx, cy+4);
}
```

### Same-file controls (always include)
```html
<div id="controls">
  <button id="btnPlay">▶ 播放</button>
  <button id="btnPause" disabled>⏸ 暂停</button>
  <button id="btnRestart">⟲ 重播</button>
  <span id="progress">00:00 / 02:30</span>
</div>

<script>
// Keyboard: Space = play/pause, ←/→ = skip segment, click = seek
document.addEventListener('keydown', e => {
  if(e.key === ' ') { e.preventDefault(); togglePlay(); }
  if(e.key === 'ArrowRight') skipToNextSegment();
  if(e.key === 'ArrowLeft') skipToPrevSegment();
});
canvas.addEventListener('click', e => {
  const pct = (e.clientX - canvas.getBoundingClientRect().left) / canvas.width;
  t = pct * TOTAL_TIME;
});
</script>
```

## Government video styling constants (for reference)
```javascript
const GOLD = '#c9a84c';
const GOLD_LIGHT = '#e8d5a3';
const DARK_BG = '#0a1626';
const DARK2 = '#071220';
const DARK3 = '#122a3e';
const TEXT_LIGHT = '#bfd4e8';
const TEXT_MUTED = '#6d8aa8';
const FONT_GOV = '"Microsoft YaHei","SimHei",sans-serif';
```
