export default function CanvasLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div style={{ margin: 0, padding: 0, overflowX: "hidden" }}>{children}</div>
  )
}
