import { ui, defaultLang } from './ui';

export function useTranslations(lang: keyof typeof ui) {
  return function t(key: string) {
    if (lang in ui && key in ui[lang]) {
      return ui[lang][key as keyof (typeof ui)[typeof lang]];
    }
    if (key in ui[defaultLang]) {
      return ui[defaultLang][key as keyof (typeof ui)[typeof defaultLang]];
    }
    return key;
  };
}
