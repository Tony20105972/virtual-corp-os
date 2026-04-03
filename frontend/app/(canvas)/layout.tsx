export default function CanvasLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div style={{ margin: 0, padding: 0, overflow: "hidden" }}>{children}</div>
  )
}
