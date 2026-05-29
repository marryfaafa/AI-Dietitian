<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useReveal } from '@/composables/useReveal'
const router = useRouter()
const { isVisible } = useReveal()
const scrollY = ref(0)
window.addEventListener('scroll', () => scrollY.value = window.scrollY, { passive: true })
</script>

<template>
  <div class="landing">
    <!-- ── 导航 ── -->
    <header class="ln-header">
      <span class="ln-logo">膳养</span>
      <div class="ln-nav">
        <span>体质科学</span>
        <span>知识图谱</span>
        <span>智能配餐</span>
        <button class="ln-btn-outline" @click="router.push('/login')">登录</button>
        <button class="ln-btn" @click="router.push('/register')">免费注册</button>
      </div>
    </header>

    <!-- ── HERO ── -->
    <section class="ln-hero">
      <div class="ln-hero-bg">
        <div class="ln-orb o1"></div>
        <div class="ln-orb o2"></div>
        <div class="ln-grid"></div>
      </div>
      <div class="ln-hero-body">
        <div class="ln-hero-tag">自然 · 科学 · 个性化</div>
        <h1 class="ln-hero-title" :style="{ transform: `translateY(${scrollY * 0.08}px)` }">
          你的膳食<br />
          <span class="ln-hero-em">独一无二</span>
        </h1>
        <p class="ln-hero-sub">
          基于知识图谱的 RAG 智能引擎，融合中医体质辨识与现代营养科学<br />为每一位用户生成专属的、合规的膳食方案
        </p>
        <div class="ln-hero-cta">
          <button class="ln-btn ln-btn-lg" @click="router.push('/login')">开启膳养之旅</button>
          <span class="ln-hero-hint">已有账号？<a @click="router.push('/login')">登录</a></span>
        </div>
        <div class="ln-scroll-hint">⌄</div>
      </div>
    </section>

    <!-- ── FEATURES ── -->
    <section class="ln-sec">
      <div class="ln-sec-inner">
        <div class="ln-sec-head" data-rv="ft-h" :class="{ on: isVisible('ft-h') }">
          <span class="ln-sec-tag">核心能力</span>
          <h2>这正是你需要的</h2>
        </div>
        <div class="ln-cards">
          <div class="ln-card" data-rv="ft-1" :class="{ on: isVisible('ft-1') }">
            <span class="ln-card-icon">🧬</span>
            <h3>九种体质精准辨识</h3>
            <p>基于中医经典理论，智能分析平和质、气虚质、阳虚质等九种体质特征，精准匹配饮食宜忌</p>
            <div class="ln-card-tag">180+ 食材映射</div>
          </div>
          <div class="ln-card ln-card-feat" data-rv="ft-2" :class="{ on: isVisible('ft-2') }">
            <span class="ln-card-icon">🔬</span>
            <h3>知识图谱推理引擎</h3>
            <p>食材→营养→体质→禁忌四层关联，支持多跳推理，实现传统关键词匹配无法达到的理解深度</p>
            <div class="ln-card-tag">Neo4j + Milvus</div>
          </div>
          <div class="ln-card" data-rv="ft-3" :class="{ on: isVisible('ft-3') }">
            <span class="ln-card-icon">🍽️</span>
            <h3>AI 智能配餐规划</h3>
            <p>根据你的体质、病症、忌口，LLM 大模型自动生成一日三餐和一周食谱，每道菜附合规评分</p>
            <div class="ln-card-tag">Kimi-K2 大模型</div>
          </div>
        </div>
      </div>
    </section>

    <!-- ── HOW ── -->
    <section class="ln-sec ln-sec-alt">
      <div class="ln-sec-inner">
        <div class="ln-sec-head" data-rv="hw-h" :class="{ on: isVisible('hw-h') }">
          <span class="ln-sec-tag">使用流程</span>
          <h2>简单三步，开启个性化膳食</h2>
        </div>
        <div class="ln-steps">
          <div class="ln-step" data-rv="hw-1" :class="{ on: isVisible('hw-1') }">
            <div class="ln-step-num">01</div>
            <h4>完善健康画像</h4>
            <p>选择你的体质类型、健康关注和饮食限制，建立专属营养档案</p>
          </div>
          <div class="ln-step-arrow">→</div>
          <div class="ln-step" data-rv="hw-2" :class="{ on: isVisible('hw-2') }">
            <div class="ln-step-num">02</div>
            <h4>AI 智能分析</h4>
            <p>知识图谱实时交叉比对，秒级完成食材合规检查与营养评估</p>
          </div>
          <div class="ln-step-arrow">→</div>
          <div class="ln-step" data-rv="hw-3" :class="{ on: isVisible('hw-3') }">
            <div class="ln-step-num">03</div>
            <h4>获取专属方案</h4>
            <p>每日更新三餐推荐，随时与 AI 营养顾问交流，持续优化</p>
          </div>
        </div>
      </div>
    </section>

    <!-- ── CTA ── -->
    <section class="ln-cta">
      <div class="ln-cta-inner" data-rv="cta" :class="{ on: isVisible('cta') }">
        <h2>让每一餐，都精准地属于你</h2>
        <p>不是千篇一律的推荐，而是基于你的独特体质，生成独一无二的膳食方案</p>
        <button class="ln-btn ln-btn-lg" @click="router.push('/login')">免费开始</button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.landing { background: var(--c-bg); font-family: var(--font-body); overflow-x: hidden }
/* nav */
.ln-header { display: flex; align-items: center; justify-content: space-between; padding: 0 40px; height: 64px; position: sticky; top: 0; z-index: 100; background: rgba(249,246,240,.8); backdrop-filter: blur(12px); border-bottom: 1px solid var(--c-border-light) }
.ln-logo { font: 900 22px var(--font-display); color: var(--c-primary); letter-spacing: .05em }
.ln-nav { display: flex; align-items: center; gap: 28px }
.ln-nav span { font-size: 13px; color: var(--c-ink-soft); font-weight: 500; cursor: default }
.ln-btn-outline { padding: 8px 18px; border-radius: var(--r-sm); background: transparent; border: 1.5px solid var(--c-border); font-size: 13px; font-weight: 500; color: var(--c-ink); transition: all .2s }
.ln-btn-outline:hover { border-color: var(--c-primary); color: var(--c-primary) }
.ln-btn { padding: 10px 22px; border-radius: var(--r-sm); background: var(--c-primary); color: white; font-size: 13px; font-weight: 600; transition: all .2s; letter-spacing: .02em }
.ln-btn:hover { background: var(--c-primary-light); transform: translateY(-1px) }
.ln-btn-lg { padding: 16px 40px; font-size: 17px; border-radius: var(--r); font-family: var(--font-display) }
/* hero */
.ln-hero { position: relative; min-height: 92vh; display: flex; align-items: center; justify-content: center; overflow: hidden;
  background: radial-gradient(ellipse 100% 70% at 50% 0%, rgba(61,94,58,.06) 0%, transparent 60%),
              radial-gradient(ellipse 60% 40% at 80% 80%, rgba(184,155,114,.06) 0%, transparent 50%) }
.ln-hero-bg { position: absolute; inset: 0 }
.ln-orb { position: absolute; border-radius: 50% }
.ln-orb.o1 { width: 600px; height: 600px; top: -100px; right: -100px; background: radial-gradient(circle, rgba(212,120,60,.04) 0%, transparent 60%); animation: orb 20s ease-in-out infinite }
.ln-orb.o2 { width: 400px; height: 400px; bottom: -50px; left: -80px; background: radial-gradient(circle, rgba(61,94,58,.05) 0%, transparent 60%); animation: orb 24s ease-in-out infinite reverse }
@keyframes orb { 0%,100%{ transform: translate(0,0) } 33%{ transform: translate(30px,-20px) } 66%{ transform: translate(-20px,15px) } }
.ln-grid { position: absolute; inset: 0; background-image: linear-gradient(rgba(0,0,0,.015) 1px, transparent 1px), linear-gradient(90deg, rgba(0,0,0,.015) 1px, transparent 1px); background-size: 64px 64px;
  mask-image: radial-gradient(ellipse 70% 50% at 50% 50%, black 30%, transparent 80%); -webkit-mask-image: radial-gradient(ellipse 70% 50% at 50% 50%, black 30%, transparent 80%) }
.ln-hero-body { position: relative; z-index: 2; text-align: center; padding: 24px }
.ln-hero-tag { font-size: 11px; font-weight: 600; letter-spacing: .2em; text-transform: uppercase; color: var(--c-accent); margin-bottom: 24px }
.ln-hero-title { font: 900 clamp(52px, 10vw, 110px)/1.05 var(--font-display); letter-spacing: -.025em; color: var(--c-ink); margin-bottom: 24px }
.ln-hero-em { color: var(--c-accent); font-style: italic }
.ln-hero-sub { font-size: 17px; line-height: 1.9; color: var(--c-ink-muted); max-width: 600px; margin: 0 auto 40px; font-weight: 300 }
.ln-hero-cta { display: flex; flex-direction: column; align-items: center; gap: 14px; animation: fadeUp 1s .2s both; }
@keyframes fadeUp { from{ opacity:0; transform:translateY(20px) } to{ opacity:1; transform:translateY(0) } }
.ln-hero-hint { font-size: 13px; color: var(--c-ink-muted) }
.ln-hero-hint a { color: var(--c-accent); cursor: pointer; font-weight: 600 }
.ln-scroll-hint { position: absolute; bottom: 32px; left: 50%; transform: translateX(-50%); font-size: 24px; color: var(--c-ink-muted); animation: bounce 2s ease-in-out infinite }
@keyframes bounce { 0%,100%{ transform: translateX(-50%) translateY(0) } 50%{ transform: translateX(-50%) translateY(8px) } }

/* sections */
.ln-sec { padding: 120px 24px }
.ln-sec-alt { background: var(--c-bg-alt) }
.ln-sec-inner { max-width: 1100px; margin: 0 auto }
.ln-sec-head { text-align: center; margin-bottom: 64px; opacity:0; transform:translateY(32px); transition: all .8s var(--ease) }
.ln-sec-head.on { opacity:1; transform:translateY(0) }
.ln-sec-tag { display: inline-block; padding: 4px 12px; border-radius: 20px; background: var(--c-accent-bg); color: var(--c-accent); font-size: 11px; font-weight: 600; letter-spacing: .1em; margin-bottom: 12px }
.ln-sec-head h2 { font: 700 clamp(28px,4vw,44px)/1.25 var(--font-display); color: var(--c-ink); letter-spacing: -.01em }

/* cards */
.ln-cards { display: grid; grid-template-columns: repeat(3,1fr); gap: 20px }
.ln-card { background: var(--c-surface); border: 1px solid var(--c-border-light); border-radius: var(--r-lg); padding: 36px 28px; transition: all .35s var(--ease); opacity:0; transform:translateY(32px) }
.ln-card.on,.ln-card.on:nth-child(2) { opacity:1; transform:translateY(0) }
.ln-card:nth-child(2) { transition-delay: .12s }
.ln-card:nth-child(3) { transition-delay: .24s }
.ln-card:hover { transform: translateY(-4px); box-shadow: var(--shadow-lg); border-color: var(--c-border) }
.ln-card-feat { border-color: var(--c-primary); border-width: 2px; background: linear-gradient(170deg, var(--c-primary-bg), white) }
.ln-card-icon { font-size: 34px; display: block; margin-bottom: 20px }
.ln-card h3 { font: 600 18px var(--font-display); margin-bottom: 10px; color: var(--c-ink) }
.ln-card p { font-size: 14px; line-height: 1.75; color: var(--c-ink-soft); margin-bottom: 20px }
.ln-card-tag { display: inline-block; padding: 4px 12px; border-radius: 20px; border: 1px solid var(--c-border); font-size: 11px; color: var(--c-ink-muted) }

/* steps */
.ln-steps { display: flex; align-items: flex-start; justify-content: center; gap: 16px; flex-wrap: wrap }
.ln-step { flex: 1; min-width: 180px; max-width: 280px; text-align: center; padding: 24px; opacity:0; transform:translateY(32px); transition: all .8s var(--ease) }
.ln-step.on,.ln-step.on:nth-child(3) { opacity:1; transform:translateY(0) }
.ln-step:nth-child(3) { transition-delay: .12s }
.ln-step:nth-child(5) { transition-delay: .24s }
.ln-step-num { font: 900 48px var(--font-display); color: var(--c-primary); opacity: .15; margin-bottom: 8px }
.ln-step h4 { font: 600 16px var(--font-display); margin-bottom: 6px }
.ln-step p { font-size: 13px; color: var(--c-ink-soft); line-height: 1.6 }
.ln-step-arrow { color: var(--c-border); font-size: 28px; padding-top: 48px; flex-shrink: 0 }

/* cta */
.ln-cta { padding: 140px 24px; text-align: center;
  background: radial-gradient(ellipse 100% 100% at 50% 100%, rgba(61,94,58,.06) 0%, transparent 50%),
              radial-gradient(ellipse 60% 60% at 30% 0%, rgba(212,120,60,.03) 0%, transparent 50%) }
.ln-cta-inner { opacity:0; transform:translateY(32px); transition: all .9s var(--ease) }
.ln-cta-inner.on { opacity:1; transform:translateY(0) }
.ln-cta h2 { font: 700 clamp(28px,5vw,44px)/1.3 var(--font-display); color: var(--c-ink); margin-bottom: 16px }
.ln-cta p { font-size: 16px; color: var(--c-ink-muted); margin-bottom: 36px }

@media(max-width:768px){ .ln-cards{ grid-template-columns:1fr } .ln-header{ padding:0 16px } .ln-nav{ display:none } }
</style>
