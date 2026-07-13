import Providers from "./components/Providers";
import Nav from "./components/Nav";
import AuthGate from "./components/AuthGate";

export const metadata = {
  title: "reviewiq",
  description: "AI review intelligence dashboard",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body style={{ margin: 0, background: "#faf9f6", color: "#222" }}>
        <Providers>
          <Nav />
          <AuthGate>{children}</AuthGate>
        </Providers>
      </body>
    </html>
  );
}
