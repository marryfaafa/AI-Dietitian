import { ref, onMounted, onUnmounted } from 'vue'

export function useReveal() {
  const revealed = ref(new Set<string>())
  let obs: IntersectionObserver | null = null

  onMounted(() => {
    obs = new IntersectionObserver((entries) => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          const id = e.target.getAttribute('data-rv')
          if (id) revealed.value.add(id)
          obs?.unobserve(e.target)
        }
      })
    }, { threshold: 0.15 })
    document.querySelectorAll('[data-rv]').forEach(el => obs?.observe(el))
  })
  onUnmounted(() => obs?.disconnect())

  return { revealed, isVisible: (id: string) => revealed.value.has(id) }
}
