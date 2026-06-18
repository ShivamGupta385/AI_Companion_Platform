import DocumentUploader from "./DocumentUploader";
import DocumentList from "./DocumentList";

interface RagSidebarProps {

  selectedDocumentId:
    string | null;

  onSelectDocument: (
    id: string,
    name: string
  ) => void;

}

export default function RagSidebar({
  selectedDocumentId,
  onSelectDocument
}: RagSidebarProps) {

  return (

    <div
      className="
        w-80
        h-screen
        bg-white
        border-r
        flex
        flex-col
      "
    >

      {/* Header */}
      <div className="p-6 border-b">

        <h2 className="text-2xl font-bold text-gray-900">
          📚 Knowledge Base
        </h2>

        <p className="text-sm text-gray-500 mt-1">
          Upload and manage your documents
        </p>

      </div>

      {/* Content */}
      <div className="flex-1 p-6 overflow-y-auto">

        <DocumentUploader />

        <div className="mt-8">

          <DocumentList
            selectedDocumentId={
              selectedDocumentId
            }
            onSelect={
              onSelectDocument
            }
          />

        </div>

      </div>

    </div>

  );
}