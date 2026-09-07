// Cloudflare Pages Functions 中间件：整站 Basic Auth（用户名/密码）
// 密码在 Pages 项目的环境变量里配置（不要写进代码）：
//   REVIEW_USER / REVIEW_PASS
// 评审或自用都走同一套账密；401 时浏览器会弹出登录框。
export async function onRequest({ request, env, next }) {
  const user = env.REVIEW_USER || '';
  const pass = env.REVIEW_PASS || '';
  if (!user || !pass) {
    return new Response('REVIEW_USER/REVIEW_PASS not configured', { status: 500 });
  }
  const auth = request.headers.get('Authorization') || '';
  const expected = 'Basic ' + btoa(user + ':' + pass);
  if (auth !== expected) {
    return new Response('Unauthorized', {
      status: 401,
      headers: { 'WWW-Authenticate': 'Basic realm="bjcp review"' },
    });
  }
  return next(request);
}
