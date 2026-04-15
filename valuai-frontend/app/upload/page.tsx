import UploadWizard from "@/components/UploadWizard";

export default function UploadPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-10">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-extrabold text-gray-900 mb-2">New Business Valuation</h1>
        <p className="text-gray-500 text-sm">
          Complete the 9-step wizard to generate your AI-powered valuation report.
        </p>
      </div>
      <UploadWizard />
    </div>
  );
}
