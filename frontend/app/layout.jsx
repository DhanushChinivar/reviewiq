import "./globals.css";
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
      <body>
        <Providers>
          <Nav />
          <AuthGate>{children}</AuthGate>
        </Providers>
      </body>
    </html>
  );
}
