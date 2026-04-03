export const runtime = "edge"

export async function GET() {
  return new Response("SSE endpoint — Day 5에서 구현 예정", { status: 200 })
}
