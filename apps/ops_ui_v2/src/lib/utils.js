export function cn(...classes) {
  return classes.filter(Boolean).join(' ');
}

export const getResponsiveClass = (mobile, tablet, desktop) => {
  return `${mobile} md:${tablet} lg:${desktop}`;
};
