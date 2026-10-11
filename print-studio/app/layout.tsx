import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Vale Meridian | Print Studio',
  description: 'Review, prepare and print the Vale Meridian evening.',
  robots: { index: false, follow: false },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
