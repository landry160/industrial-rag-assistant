export const metadata = {
  title: "Industrial RAG Assistant",
  description: "Ask technical questions — answers grounded in your plant documentation.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body style={{ fontFamily: "system-ui, sans-serif", margin: 0 }}>{children}</body>
    </html>
  );
}
