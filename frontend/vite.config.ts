/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    // Vite 8 minifies CSS with Lightning CSS, which drops any property the
    // build target does not claim to support. The default target predates
    // backdrop-filter, so the glass surfaces shipped as plain translucent
    // panels with no blur at all and nothing warned about it. These four
    // are the oldest engines with unprefixed backdrop-filter.
    cssTarget: ['chrome76', 'edge79', 'firefox103', 'safari18'],
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
  },
})
