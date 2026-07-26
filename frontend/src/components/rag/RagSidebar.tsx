import DocumentUploader from "./DocumentUploader";
import DocumentList from "./DocumentList";

interface RagSidebarProps {
  selectedDocumentId: string | null;

  onSelectDocument: (
    id: string,
    name: string
  ) => void;
  companionId?: string;
}

export default function RagSidebar({
  selectedDocumentId,
  onSelectDocument,
  companionId,
}: RagSidebarProps) {
  return (
    <div
      className="
        w-[340px]
        h-screen
        bg-white
        border-l
        border-[#ECEAF4]
        flex
        flex-col
      "
    >
      {/* Header */}
      <div className="px-6 py-6 border-b border-[#ECEAF4]">

        <div className="flex items-center gap-3">

          <div
            className="
              w-12
              h-12
              rounded-2xl
              bg-violet-100
              flex
              items-center
              justify-center
              text-xl
            "
          >
            📚
          </div>

          <div>
            <h2
              className="
                text-xl
                font-bold
                text-slate-900
              "
            >
              Knowledge Base
            </h2>

            <p
              className="
                text-sm
                text-slate-500
                mt-1
              "
            >
              Enhance your AI companion
            </p>
          </div>

        </div>

      </div>

      {/* Content */}
      <div
        className="
          flex-1
          overflow-y-auto
          p-5
          space-y-5
        "
      >

        {/* Upload Section */}
        <div
          className="
            bg-[#F8F7FC]
            border
            border-[#ECEAF4]
            rounded-3xl
            p-4
          "
        >
          <h3
            className="
              text-sm
              font-semibold
              text-slate-700
              mb-3
            "
          >
            Upload Documents
          </h3>
          <DocumentUploader />
        </div>

        {/* Documents Section */}
        <div
          className="
            bg-white
            border
            border-[#ECEAF4]
            rounded-3xl
            p-4
          "
        >
          <div
            className="
              flex
              items-center
              justify-between
              mb-4
            "
          >
            <h3
              className="
                text-sm
                font-semibold
                text-slate-700
              "
            >
              Documents
            </h3>

            <span
              className="
                text-xs
                text-violet-600
                font-medium
              "
            >
              RAG Ready
            </span>
          </div>

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

      {/* Footer */}
      <div
        className="
          border-t
          border-[#ECEAF4]
          p-5
        "
      >
        <div
          className="
            rounded-2xl
            bg-violet-50
            px-4
            py-3
          "
        >
          <p
            className="
              text-xs
              text-violet-700
              leading-relaxed
            "
          >
            Selected documents will be
            used for Retrieval-Augmented
            Generation (RAG) responses.
          </p>
        </div>
      </div>

    </div>
  );
}