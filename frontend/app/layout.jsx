export const metadata = {
  title: "reviewiq",
  description: "AI review intelligence dashboard",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body style={{ margin: 0, background: "#faf9f6", color: "#222" }}>
        {children}
      </body>
    </html>
  );
}
