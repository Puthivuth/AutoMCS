import Link from "next/link";
export default function Brand() {
  return (<Link href="/" className="flex items-baseline gap-2 whitespace-nowrap">
    <span className="text-xl font-bold tracking-tight">Auto<span className="text-brand">MCS</span></span>
    <span className="hidden text-xs font-normal text-muted sm:inline">by Puthivuth Chhoeun</span></Link>);
}
