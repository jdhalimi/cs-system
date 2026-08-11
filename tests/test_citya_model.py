from cs_system.connectors.citya import CityaDocument


def test_citya_document_sanitizes_a_path_for_windows():
    document = CityaDocument("Facture: A/B", "pdf", "id-1", ("Immeuble", "Factures 2026"))
    assert document.relative_path.as_posix() == "Immeuble/Factures 2026/Facture_ A_B.pdf"
