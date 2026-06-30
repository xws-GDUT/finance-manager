import '@testing-library/jest-dom'

// Mock matchMedia for antd responsive components
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
});

// Mock getComputedStyle for antd components
const originalGetComputedStyle = window.getComputedStyle;
window.getComputedStyle = (elt: Element, pseudoElt?: string | null) => {
  const style = originalGetComputedStyle(elt, pseudoElt);
  if (pseudoElt) {
    // Return a minimal CSSStyleDeclaration for pseudo-elements
    return {
      getPropertyValue: () => '',
      length: 0,
    } as unknown as CSSStyleDeclaration;
  }
  return style;
};

// Mock ResizeObserver for antd Table, Tree, and other components
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}
window.ResizeObserver = ResizeObserverMock as unknown as typeof ResizeObserver;
