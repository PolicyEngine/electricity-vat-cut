import PolicyEngineFooter from "../src/components/PolicyEngineFooter";
import PolicyEngineHeader from "../src/components/PolicyEngineHeader";

import Script from "next/script";

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
        {/* Google Analytics: policyengine.org's GA4 property; this app is served at policyengine.org/uk/electricity-vat-cut through a rewrite, where the main site's GA does not reach. */}
        {process.env.NODE_ENV === "production" && (
          <>
            <Script
              src="https://www.googletagmanager.com/gtag/js?id=G-2YHG89FY0N"
              strategy="afterInteractive"
            />
            <Script id="google-analytics" strategy="afterInteractive">
              {`window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}
gtag('js', new Date());
gtag('config', 'G-2YHG89FY0N');`}
            </Script>
          </>
        )}
      </body>
    </html>
  );
}
