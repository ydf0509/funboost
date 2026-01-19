import type { Metadata } from "next";
import { Noto_Sans_SC, Orbitron } from "next/font/google";
import "./globals.css";
import { ThemeInitializer } from "@/components/layout/ThemeInitializer";

const notoSans = Noto_Sans_SC({
  variable: "--font-body",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
});

const orbitron = Orbitron({
  variable: "--font-display",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "Funboost 管理控制台",
  description: "Funboost 分布式函数的监控与管理中心。",
};

// 阻塞式脚本：在 CSS 解析前设置主题，防止闪烁
const themeScript = `
(function() {
  var d = document.documentElement;
  var t = localStorage.getItem('funboost-theme');
  if (!t) t = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  d.setAttribute('data-theme', t);
  d.style.colorScheme = t;
})();
`;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN" data-theme="light" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body className={`${notoSans.variable} ${orbitron.variable} antialiased`}>
        <ThemeInitializer />
        {children}
      </body>
    </html>
  );
}
