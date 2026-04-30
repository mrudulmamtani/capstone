export default function ApproachDiagram() {
  return (
    <div className="card p-5 space-y-4">
      <div className="flex items-center justify-between gap-4">
        <div>
          <div className="text-sm text-ink-500">System approach</div>
          <h2 className="text-xl font-semibold">Physical blueprint ? SOP fusion pipeline</h2>
          <div className="mt-1 text-sm text-ink-500">
            This is the review story: spatial traces are parsed from blueprint geometry, fused with SOP logic and operational context, and rendered back as a live heatmap + simulation network.
          </div>
        </div>
        <div className="badge bg-sky-100 text-sky-700 px-3 py-1.5 rounded-full">Capstone architecture</div>
      </div>

      <div className="overflow-hidden rounded-2xl border border-ink-100 bg-slate-50 p-4">
        <svg viewBox="0 0 1200 520" className="w-full">
          <defs>
            <linearGradient id="panel" x1="0%" x2="100%">
              <stop offset="0%" stopColor="#eff6ff" />
              <stop offset="100%" stopColor="#ffffff" />
            </linearGradient>
            <linearGradient id="fusion" x1="0%" x2="100%">
              <stop offset="0%" stopColor="#fef3c7" />
              <stop offset="100%" stopColor="#fff7ed" />
            </linearGradient>
            <marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto">
              <path d="M0,0 L10,5 L0,10 z" fill="#2563eb" />
            </marker>
          </defs>

          <rect x="20" y="36" width="210" height="132" rx="18" fill="url(#panel)" stroke="#93c5fd" strokeWidth="2" />
          <text x="40" y="72" fontSize="18" fontWeight="700" fill="#0f172a">Physical Space</text>
          <rect x="48" y="88" width="150" height="56" rx="10" fill="#ffffff" stroke="#cbd5e1" />
          <text x="62" y="116" fontSize="13" fill="#334155">live shop-floor geometry,</text>
          <text x="62" y="134" fontSize="13" fill="#334155">operator motion, tool activity</text>

          <rect x="334" y="40" width="210" height="94" rx="18" fill="url(#panel)" stroke="#93c5fd" strokeWidth="2" />
          <text x="356" y="74" fontSize="18" fontWeight="700" fill="#0f172a">ML Spatial Mapping</text>
          <text x="356" y="100" fontSize="13" fill="#334155">detectors, pose graphs,</text>
          <text x="356" y="118" fontSize="13" fill="#334155">zone parsing, coordinates</text>

          <rect x="374" y="156" width="164" height="62" rx="14" fill="#ffffff" stroke="#93c5fd" strokeWidth="2" />
          <text x="395" y="190" fontSize="15" fontWeight="600" fill="#0f172a">AutoCAD Parsing</text>
          <text x="395" y="208" fontSize="12" fill="#475569">geometry formalization</text>

          <rect x="622" y="38" width="202" height="76" rx="18" fill="#ecfeff" stroke="#5eead4" strokeWidth="2" />
          <text x="646" y="70" fontSize="18" fontWeight="700" fill="#0f172a">Organizational Context</text>
          <text x="646" y="94" fontSize="13" fill="#334155">roles, station rules</text>

          <rect x="622" y="132" width="202" height="76" rx="18" fill="#ecfeff" stroke="#5eead4" strokeWidth="2" />
          <text x="678" y="166" fontSize="18" fontWeight="700" fill="#0f172a">ERP Ledgers</text>
          <text x="662" y="190" fontSize="13" fill="#334155">orders, batches, timing</text>

          <rect x="942" y="44" width="214" height="104" rx="18" fill="#fef3c7" stroke="#f59e0b" strokeWidth="2" />
          <text x="1008" y="78" fontSize="18" fontWeight="700" fill="#0f172a">SOP Map</text>
          <text x="970" y="104" fontSize="13" fill="#334155">JSON procedure graph</text>
          <text x="970" y="122" fontSize="13" fill="#334155">step sequence, roles,</text>
          <text x="970" y="140" fontSize="13" fill="#334155">timing, validation</text>

          <rect x="706" y="242" width="248" height="72" rx="18" fill="url(#fusion)" stroke="#f59e0b" strokeWidth="2" />
          <text x="742" y="276" fontSize="19" fontWeight="700" fill="#0f172a">Spatial + Procedural Fusion</text>
          <text x="758" y="298" fontSize="13" fill="#334155">simulation engine + blueprint heat synthesis</text>

          <rect x="88" y="330" width="356" height="154" rx="18" fill="#ffffff" stroke="#cbd5e1" strokeWidth="2" />
          <text x="198" y="356" fontSize="18" fontWeight="700" fill="#0f172a">Blueprint Output</text>
          <rect x="140" y="376" width="248" height="94" rx="12" fill="#f8fafc" stroke="#94a3b8" />
          <line x1="164" y1="390" x2="360" y2="390" stroke="#cbd5e1" />
          <line x1="164" y1="412" x2="360" y2="412" stroke="#cbd5e1" />
          <line x1="164" y1="434" x2="360" y2="434" stroke="#cbd5e1" />
          <line x1="208" y1="388" x2="208" y2="462" stroke="#cbd5e1" />
          <line x1="266" y1="388" x2="266" y2="462" stroke="#cbd5e1" />
          <line x1="322" y1="388" x2="322" y2="462" stroke="#cbd5e1" />

          <rect x="784" y="330" width="346" height="154" rx="18" fill="#ffffff" stroke="#cbd5e1" strokeWidth="2" />
          <text x="896" y="356" fontSize="18" fontWeight="700" fill="#0f172a">Heatmap Output</text>
          <rect x="836" y="376" width="240" height="94" rx="12" fill="#f8fafc" stroke="#94a3b8" />
          <rect x="850" y="390" width="212" height="66" rx="8" fill="url(#fusion)" opacity="0.92" />
          <circle cx="900" cy="420" r="18" fill="#2563eb" opacity="0.55" />
          <circle cx="950" cy="430" r="24" fill="#22c55e" opacity="0.4" />
          <circle cx="1018" cy="414" r="26" fill="#f97316" opacity="0.55" />
          <circle cx="1045" cy="397" r="22" fill="#dc2626" opacity="0.6" />

          <line x1="230" y1="102" x2="334" y2="88" stroke="#2563eb" strokeWidth="3" markerEnd="url(#arrow)" />
          <line x1="438" y1="134" x2="438" y2="156" stroke="#2563eb" strokeWidth="3" markerEnd="url(#arrow)" />
          <line x1="544" y1="88" x2="622" y2="76" stroke="#2563eb" strokeWidth="3" markerEnd="url(#arrow)" />
          <line x1="544" y1="108" x2="622" y2="164" stroke="#2563eb" strokeWidth="3" markerEnd="url(#arrow)" />
          <line x1="824" y1="76" x2="942" y2="96" stroke="#2563eb" strokeWidth="3" markerEnd="url(#arrow)" />
          <line x1="824" y1="170" x2="942" y2="120" stroke="#2563eb" strokeWidth="3" markerEnd="url(#arrow)" />
          <line x1="512" y1="206" x2="706" y2="278" stroke="#2563eb" strokeWidth="3" markerEnd="url(#arrow)" />
          <line x1="1070" y1="148" x2="930" y2="242" stroke="#2563eb" strokeWidth="3" markerEnd="url(#arrow)" />
          <line x1="772" y1="314" x2="402" y2="330" stroke="#2563eb" strokeWidth="3" markerEnd="url(#arrow)" />
          <line x1="908" y1="314" x2="948" y2="330" stroke="#2563eb" strokeWidth="3" markerEnd="url(#arrow)" />
        </svg>
      </div>
    </div>
  );
}
