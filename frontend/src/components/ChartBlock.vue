<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import * as echarts from 'echarts/core'
import { BarChart } from 'echarts/charts'
import { GridComponent, TitleComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([BarChart, GridComponent, TitleComponent, TooltipComponent, CanvasRenderer])

const props = defineProps({ chart: { type: Object, required: true } })
const el = ref(null)
let inst = null

function render() {
  if (!el.value) return
  if (!inst) inst = echarts.init(el.value)
  const data = props.chart.data || []
  inst.setOption(
    {
      title: { text: props.chart.title || '', left: 'center', textStyle: { fontSize: 13, color: '#1d2129' } },
      tooltip: { trigger: 'axis' },
      grid: { left: 52, right: 16, top: 44, bottom: data.length > 6 ? 72 : 56 },
      xAxis: {
        type: 'category',
        data: data.map((d) => d.label),
        axisLabel: { interval: 0, rotate: data.length > 6 ? 30 : 0, fontSize: 11 },
      },
      yAxis: { type: 'value', name: props.chart.y_label || '', nameTextStyle: { fontSize: 11 } },
      series: [
        {
          type: props.chart.chart_type || 'bar',
          data: data.map((d) => d.value),
          itemStyle: { color: '#3370ff', borderRadius: [3, 3, 0, 0] },
          label: { show: true, position: 'top', fontSize: 11 },
        },
      ],
    },
    true
  )
}

onMounted(render)
watch(() => props.chart, render, { deep: true })
onBeforeUnmount(() => {
  if (inst) {
    inst.dispose()
    inst = null
  }
})
</script>

<template>
  <div ref="el" class="chart-block"></div>
</template>

<style scoped>
.chart-block {
  width: 100%;
  height: 260px;
  margin-top: 8px;
}
</style>
