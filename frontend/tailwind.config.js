/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#f9f9f7', // off-white
        foreground: '#111111', // deep black
        accent: '#ea580c', // warm orange
      }
    },
  },
  plugins: [],
}
