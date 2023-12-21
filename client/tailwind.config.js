/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {},
  },
  plugins: [require("daisyui")],
  daisyui: {
    themes: [
      "light",
      "wireframe",
      "acid",
      "corporate",
      "nord",
      "fantasy",
      "pastel",
      "winter",
      "cyberpunk",
      "valentine",
      "dark",
      "business",
      "dracula",
      "halloween",
      "dim",
      "sunset",
    ],
  },
};
