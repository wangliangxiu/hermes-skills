# Image Prompt Generation for WeChat Long-Images

When the active model cannot generate images (e.g. DeepSeek), use this prompt-writing technique to feed external tools (WorkBuddy, CodeBuddy, Midjourney, etc.).

## Prompt Structure

Each prompt must include these sections:

### 1. Perspective / Framing
- "从蒸汽火车的厚木窗框往外看" (window narrative technique)
- "从绿皮火车的车窗望出去"
- "从高铁的宽大车窗往外看"

### 2. Three-layer scene composition
- **近景 (Foreground):** window frame, interior details, seat corner
- **中景 (Midground):** station, city, railway tracks
- **远景 (Background):** mountains, sky, distant cityscape

### 3. Color / Tone
- One sentence specifying the overall palette
- Examples: "棕褐色系，像染了茶色的老照片", "军绿＋灰黄＋暖棕", "暖橙＋淡紫晚霞"

### 4. Style directive
- For narrative/educational content: "手绘插画/绘本风，不追求写实"
- Append storytelling language: "像一本给大人看的绘本"

### 5. Aspect ratio
- 3:4 for WeChat portrait mode
- Horizontal for album/cinematic mode

### 6. Special notes for transition pages
- "高度是正图的一半"
- "背景颜色从上图的{color}渐变到下图的{color}"
- "画面中没有任何文字"

## File delivery rule

- **Always use .txt extension** — the user explicitly rejected .md files because Windows sometimes doesn't associate them with an editor. .txt opens correctly in Notepad. NEVER save as .md or .html for prompt delivery files. Exception: HTML preview files (not prompts) can be .html.
- Save to Desktop under `C:\Users\使用者\Desktop\`

## WorkBuddy prompt-writing experience (June 2026)

When writing prompts for WorkBuddy (腾讯CodeBuddy), the user found that:
- **Long detailed prompts with many sections sometimes confuse the AI** — it may misinterpret key objects (e.g. "集装箱式" was read as a literal shipping container, producing a box with a corrugated roof instead of an open-top coal wagon).
- **Short, precise keyword combinations work better** than paragraph-style descriptions for WorkBuddy.
- **Avoid ambiguous analogies** — "像集装箱一样" can lead the AI to generate a literal cargo shipping container rather than the intended train wagon.
- **Use direct railway terminology** — "敞车" (open-top wagon), "无顶盖货斗" (open cargo box), "铆接铁板" (riveted iron plates), "侧面对开铁门" (side double doors).
- **Add explicit negations** for common AI misinterpretations: "NOT a shipping container", "not a modern container" — these help steer the model away from its default associations.
- **Style keywords before content keywords** — WorkBuddy seems to process style directives better when they come first or are clearly separated.
- **Cartoon/illustration style is preferred** — the user found that photorealistic prompts produced detail-inaccurate images that were obvious and jarring. Cartoon style ("手绘插画/绘本风") gives more room for interpretation.

### ⚠️ CRITICAL: Prompt-crafting rules (taught June 2026)

These rules directly address common AI image model failures. Apply them to every prompt:

**Rule 1: Visualize text-bearing elements (AI can't render readable text)**
- ❌ "站名牌" → AI draws garbled/chinese/nonsense text
- ✅ "水泥柱顶端有风化褪色的模糊色块，已看不清原来写的是什么，只能辨识出那是旧时站牌的轮廓"
- ❌ "电子显示屏" → AI draws meaningless pixel patterns
- ✅ "一块深色矩形面板反射着天光"
- ❌ "火车票上写着xx站到xx站" → AI draws unreadable text
- ✅ "票面上原本印字的位置全部留为自然的空白或模糊色块，仿佛年代久远已褪尽了墨迹"

**Rule 2: Replace people with object traces (AI often generates deformed humans)**
- ❌ "有旅客上下车" → people may come out distorted
- ✅ "站台上散落着几只旧式编织袋和帆布行李箱，仿佛刚才还有人在这里等车"
- ❌ "乘客在站台等车"
- ✅ "站台边缘放着一只旧水壶和一卷报纸"

**Rule 3: Ground abstract time/setting with visual anchors**
- ❌ "秋天上午" → too vague, AI draws generic trees
- ✅ "深秋上午，远处几棵行道树叶子已转黄，空气中微凉清透"
- ❌ "黄昏时分"
- ✅ "夕阳把铁轨照成一条金色线，远处天空泛着紫红色"

**Rule 4: Replace comparative/quantitative descriptions with absolute visual ones**
- ❌ "比绿皮车更宽更高" → AI has no reference for what "绿皮车" looks like
- ✅ "车身宽阔高大，高出站台一截，气势明显不同于旧式列车"
- ❌ "以三百公里时速飞驰"
- ✅ "快到无法看清细节，白色车身在画面中拉出横向动感模糊线条"

**Rule 5: Replace equipment-names with pure visual description**
- ❌ "电子显示屏", "信号灯" → AI renders garbled tech artifacts
- ✅ "一块深色矩形面板反射着天光"
- ❌ "接触网电线急速掠过"
- ✅ "线缆支架和支柱急速后退，在画面边缘形成连续模糊的竖线"

**Rule 6: For fast-moving subjects, prioritize motion feel over detail**
- ❌ Describe the bullet train nose cone in detail → AI freezes the frame
- ✅ "流线型车头轮廓一闪而过来不及看清细节，视觉重心落在大面积白色车身快速滑过画面上"

**Rule 7: When describing old/museum objects, search first — don't invent specifics**
- The user explicitly corrected: "以后不要自己编，可以问我，但是不要自己编"
- Before writing a prompt about era-specific objects (trains, buildings, uniforms, vehicles), SEARCH for reference images or authoritative descriptions
- If search fails, ask a TARGETED question — don't ask expansively
- Example: "搜不到那个年代的运煤车照片，你知道大概长啥样吗？说两句就行。"
- When the user provides details, save them immediately so you don't ask again

**Rule 8: File format — ALWAYS .txt, NEVER .md**
- The user explicitly rejected .md files because Windows sometimes lacks an association
- Save prompt files as `{主题}_提示词.txt`
- Exception: HTML preview files (not prompts) can be .html

## Concrete case study: 1902 coal wagon failure (June 2026)

I wrote a prompt describing a 1902 steam-era coal wagon as "黑色集装箱式" (like a black shipping container). WorkBuddy generated a box with a corrugated roof that looked nothing like an open-top coal wagon. The user was frustrated.

**What went wrong:**
1. I used "集装箱式" as a visual analogy, but the AI model interpreted it literally as "a shipping container"
2. I didn't search for reference images or authoritative descriptions first
3. I didn't use the correct railway terminology ("敞车", "无顶盖货斗", "侧面对开铁门")

**How to prevent:**
1. Search first with keywords like "1900s 敞车 老照片 中国 铁路 侧面"
2. Use domain-specific terminology, not everyday analogies
3. Add explicit negations ("NOT a container, NOT modern freight")
4. Test the prompt; if it fails, replace analogies with precise technical terms

## File naming convention

### For single-scene prompts
Save to Desktop as `{主题}_场景{代号}_提示词.txt` (e.g. `火车长图_场景B_绿皮车.txt`)
Or `{主题}_完整提示词.txt` for all scenes combined.

### For multi-scene series (proven pattern)
Use a single file named `{主题}_完整提示词.txt` with clear separators between scenes.
Example: `火车长图_完整提示词.txt` containing all 4 eras + ending scene.
Each scene gets a header like `【场景B：1970 绿皮车】` for easy scanning.

### For transition files
Use `{主题}_过渡修改.txt` when only updating specific sections.

### ⚠️ File extension: ALWAYS .txt
This user explicitly rejected .md files. Save everything as .txt.

## Transition page elements reference
- 蒸汽火车车轮转动 → 1902→1970 transition
- 铁轨枕木快速掠过 → between historical eras
- 窗帘被风吹起 → mid-century transitions
- 窗外风景拉长模糊 → acceleration/modernity
- 车票飘落 → ending/reflection
