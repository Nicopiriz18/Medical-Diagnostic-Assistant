export const metadata = {
  title: "Medical Diagnostic Assistant",
  description: "AI-powered clinical reasoning support system",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
