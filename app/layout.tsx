import type { Metadata } from "next";
import { Provider } from "@/components/provider";
import { Shell } from "@/components/shell";
import { enabled } from "@/lib/v2/contracts";
import { cookies } from "next/headers";
import { LANG_COOKIE, parseLang } from "@/lib/lang";
import "./globals.css";
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
  const lang = parseLang((await cookies()).get(LANG_COOKIE)?.value);
  return (
    <html lang={lang}>
      <body>
        <Provider lang={lang}>
          <Shell v2Enabled={enabled()}>{children}</Shell>
        </Provider>
      </body>
    </html>
  );
}
