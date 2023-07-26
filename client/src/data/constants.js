export const baseUrl = "https://lccn.lbao.site/api/v1";

export const themes = [
  "light",
  "acid",
  "pastel",
  "fantasy",
  "autumn",
  "winter",
  "cyberpunk",
  "valentine",
  "wireframe",
  "dark",
  "dracula",
  "night",
  "halloween",
];

// trend color config of different regions
// reference: https://graphicdesign.stackexchange.com/a/118989
export const trendColorsHSLConfig = {
  default: {
    up: "120, 100%, 50%",
    down: "0, 100%, 50%",
  },
  China: {
    up: "0, 100%, 50%",
    down: "120, 100%, 50%",
  },
  Korea: {
    up: "0, 100%, 50%",
    down: "240, 100%, 50%",
  },
  Japan: {
    up: "0, 100%, 50%",
    down: "120, 100%, 50%",
  },
};
