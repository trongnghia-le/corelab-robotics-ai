import type { Metadata } from "next";
import { Provider } from "@/components/provider";
import { Shell } from "@/components/shell";
import { enabled } from "@/lib/v2/contracts";
import "./globals.css";
import "katex/dist/katex.min.css";
export const metadata: Metadata = {
  title: "CoreLab · Learn Robotics & AI",
  description:
    "Local-first learning for Robotics, Computer Vision, Reinforcement Learning and Cognitive Robotics.",
};
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <Provider>
          <Shell v2Enabled={enabled()}>{children}</Shell>
        </Provider>
      </body>
    </html>
  );
}
