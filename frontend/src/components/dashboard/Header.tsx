export default function Header() {
  return (
    <div className="mb-8 flex items-center justify-end gap-4">

      <button className="h-14 w-14 rounded-full bg-white shadow">
        🔔
      </button>

      <div className="flex items-center gap-3 rounded-full bg-white px-4 py-2 shadow">

        <img
          src="/avatar.png"
          className="h-10 w-10 rounded-full"
        />

        <span className="font-medium">
          Aarav Mehta
        </span>

      </div>

    </div>
  );
}