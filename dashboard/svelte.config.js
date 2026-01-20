import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
  preprocess: vitePreprocess(),

  kit: {
    adapter: adapter({
      fallback: 'index.html', // SPA fallback for dynamic routes
      strict: false
    }),
    paths: {
      // base is the GitHub repo name when deploying, empty for local
      base: process.env.NODE_ENV === 'production' ? '/austria-2092' : ''
    }
  }
};

export default config;
