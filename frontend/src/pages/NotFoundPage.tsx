import { Link } from "react-router-dom";

export default function NotFoundPage() {
  return (
    <div className="flex flex-col items-center gap-4 py-24 text-center">
      <h1 className="font-heading text-3xl">Page not found</h1>
      <p className="text-muted-foreground">That page doesn't exist.</p>
      <Link to="/" className="text-primary underline underline-offset-4">
        Back to Ask
      </Link>
    </div>
  );
}
