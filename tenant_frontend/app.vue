<script setup lang="ts">
import { onMounted } from 'vue'
import { useBrand } from '~/composables/useBrand'
const { load } = useBrand()
onMounted(load)
</script>

<template>
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>
</template>
