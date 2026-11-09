import type { Metadata } from "next";
import { Provider } from "@/components/provider";
import { Shell } from "@/components/shell";
import { enabled } from "@/lib/v2/contracts";
import { cookies } from "next/headers";
import { LANG_COOKIE, parseLang } from "@/lib/lang";
import { THEME_COOKIE, parseTheme } from "@/lib/theme";
// theme.css is globals.css plus the generated light theme (npm run theme).
import "@fontsource/be-vietnam-pro/400.css";
import "@fontsource/be-vietnam-pro/400-italic.css";
import "@fontsource/be-vietnam-pro/500.css";
import "@fontsource/be-vietnam-pro/600.css";
import "@fontsource/be-vietnam-pro/700.css";
// Lesson figures are drawn for Inter; see components/lesson-figure.tsx.
import "@fontsource-variable/inter";
import "./theme.css";
import "katex/dist/katex.min.css";
export const metadata: Metadata = {
  title: "CoreLab · Learn Robotics & AI",
  description:
    "Local-first learning for Robotics, Computer Vision, Reinforcement Learning and Cognitive Robotics.",
};
export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const jar = await cookies();
  const lang = parseLang(jar.get(LANG_COOKIE)?.value);
  const theme = parseTheme(jar.get(THEME_COOKIE)?.value);
  return (
    <html lang={lang} data-theme={theme}>
      <body>
        <Provider lang={lang}>
          <Shell v2Enabled={enabled()}>{children}</Shell>
        </Provider>
      </body>
    </html>
  );
}
