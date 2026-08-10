import PolicyEngineFooter from "../src/components/PolicyEngineFooter";
import PolicyEngineHeader from "../src/components/PolicyEngineHeader";

import "./globals.css";

export const metadata = {
  title: "Electricity VAT cut (5% to 0%) | PolicyEngine",
  description:
    "Interactive dashboard estimating the fiscal cost and distributional impact of the temporary VAT cut on domestic electricity (October 2026 to March 2027), using PolicyEngine UK microsimulation.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <PolicyEngineHeader />
        {children}
        <PolicyEngineFooter />
      </body>
    </html>
  );
}
