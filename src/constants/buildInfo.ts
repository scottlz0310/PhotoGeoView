export const BUILD_INFO = {
  buildTime: import.meta.env.VITE_BUILD_TIME ?? 'unknown',
  gitSha: import.meta.env.VITE_GIT_SHA ?? 'unknown',
}
