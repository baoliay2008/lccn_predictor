import { trendColorsHSLConfig } from "./data/constants";

function getTrendColorsHSL() {
  // get browser language config
  const language = navigator.language;
  // list of common primary language sub-tags:
  // https://en.wikipedia.org/wiki/IETF_language_tag#List_of_common_primary_language_subtags
  if (language.startsWith("zh")) return trendColorsHSLConfig.China;
  else if (language.startsWith("ko")) return trendColorsHSLConfig.Korea;
  else if (language.startsWith("ja")) return trendColorsHSLConfig.Japan;
  else return trendColorsHSLConfig.default;
}

export const trendColorsHSL = getTrendColorsHSL();
