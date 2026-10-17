import "./globals.css";
export const metadata = { title: "AutoMCS", description: "AI-assisted decimal table extraction and verification" };
const themeScript = `try{var t=localStorage.getItem('automcs-theme');if(t==='dark'||(!t&&matchMedia('(prefers-color-scheme:dark)').matches))document.documentElement.classList.add('dark')}catch(e){}`;
export default function Root({ children }: { children: React.ReactNode }) {
  return (<html lang="en" suppressHydrationWarning><head><script dangerouslySetInnerHTML={{ __html: themeScript }} /></head>
    <body className="font-sans">{children}</body></html>);
}
