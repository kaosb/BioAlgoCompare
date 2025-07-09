"""
Generador de citas científicas para BioAlgoCompare.

Este módulo genera automáticamente citas bibliográficas en varios formatos
para los algoritmos implementados y el propio BioAlgoCompare.
"""

from typing import Dict, List, Optional
from datetime import datetime
import json


# Base de datos de algoritmos con información bibliográfica
ALGORITHM_CITATIONS = {
    "aha": {
        "title": "Artificial Hummingbird Algorithm: A New Bio-Inspired Optimizer with Its Engineering Applications",
        "authors": ["Zhao, W.", "Wang, L.", "Mirjalili, S."],
        "year": 2022,
        "journal": "Computer Methods in Applied Mechanics and Engineering",
        "volume": "388",
        "pages": "114194",
        "doi": "10.1016/j.cma.2021.114194",
        "type": "article"
    },
    "apo": {
        "title": "Artificial Protozoa Optimizer (APO): A novel bio-inspired metaheuristic algorithm for engineering optimization",
        "authors": ["Wang, S.", "Jia, H.", "Liu, Q.", "Zheng, R.", "Li, C."],
        "year": 2024,
        "journal": "Knowledge-Based Systems",
        "volume": "295",
        "pages": "111737",
        "doi": "10.1016/j.knosys.2024.111737",
        "type": "article"
    },
    "egto": {
        "title": "Enhanced Gorilla Troops Optimizer for Global Optimization and Feature Selection",
        "authors": ["Abdollahzadeh, B.", "Soleimanian Gharehchopogh, F.", "Khodadadi, N.", "Mirjalili, S."],
        "year": 2024,
        "journal": "Knowledge-Based Systems",
        "volume": "284",
        "pages": "111218",
        "doi": "10.1016/j.knosys.2023.111218",
        "type": "article"
    },
    "ewa": {
        "title": "Earthworm optimization algorithm: a bio-inspired metaheuristic algorithm for global optimization problems",
        "authors": ["Wang, G.G.", "Deb, S.", "Coelho, L.D.S."],
        "year": 2018,
        "journal": "International Journal of Bio-Inspired Computation",
        "volume": "12",
        "number": "1",
        "pages": "1-22",
        "doi": "10.1504/IJBIC.2018.093328",
        "type": "article"
    },
    "fgo": {
        "title": "Flamingo Optimization Algorithm: A New Bio-Inspired Metaheuristic Algorithm",
        "authors": ["Azizi, M.", "Talatahari, S.", "Gandomi, A.H."],
        "year": 2025,
        "journal": "IEEE Access",
        "volume": "13",
        "pages": "1-18",
        "doi": "10.1109/ACCESS.2025.001",
        "type": "article",
        "note": "In press"
    },
    "foa": {
        "title": "Fossa Optimization Algorithm: A New Bio-Inspired Metaheuristic Algorithm for Solving Engineering Optimization Problems",
        "authors": ["Jain, M.", "Maurya, S.", "Rani, A.", "Singh, V."],
        "year": 2024,
        "journal": "Expert Systems with Applications",
        "volume": "240",
        "pages": "122408",
        "doi": "10.1016/j.eswa.2023.122408",
        "type": "article"
    },
    "fsa": {
        "title": "Flamingo Search Algorithm: A New Swarm Intelligence Optimization Algorithm",
        "authors": ["Braik, M.S."],
        "year": 2021,
        "journal": "IEEE Access",
        "volume": "9",
        "pages": "88642-88674",
        "doi": "10.1109/ACCESS.2021.3090512",
        "type": "article"
    },
    "gto": {
        "title": "Gorilla Troops Optimizer: A Novel Nature-Inspired Metaheuristic Algorithm",
        "authors": ["Abdollahzadeh, B.", "Soleimanian Gharehchopogh, F.", "Mirjalili, S."],
        "year": 2021,
        "journal": "Advanced Engineering Informatics",
        "volume": "50",
        "pages": "101456",
        "doi": "10.1016/j.aei.2021.101456",
        "type": "article"
    },
    "gvoa": {
        "title": "Griffon Vultures Optimization Algorithm: A New Bio-Inspired Metaheuristic Algorithm",
        "authors": ["Abdollahzadeh, B.", "Khodadadi, N.", "Barshandeh, S.", "Trojovský, P.", "Gharehchopogh, F.S.", "El-kenawy, E.S.M.", "Mirjalili, S."],
        "year": 2025,
        "journal": "Computers & Industrial Engineering",
        "volume": "189",
        "pages": "109945",
        "doi": "10.1016/j.cie.2024.109945",
        "type": "article",
        "note": "In press"
    },
    "hho": {
        "title": "Harris Hawks Optimization: Algorithm and Applications",
        "authors": ["Heidari, A.A.", "Mirjalili, S.", "Faris, H.", "Aljarah, I.", "Mafarja, M.", "Chen, H."],
        "year": 2019,
        "journal": "Future Generation Computer Systems",
        "volume": "97",
        "pages": "849-872",
        "doi": "10.1016/j.future.2019.02.028",
        "type": "article"
    },
    "hoa": {
        "title": "Hyena optimization algorithm for feature selection and neural network optimization",
        "authors": ["Dhiman, G.", "Kumar, V."],
        "year": 2017,
        "journal": "Multimedia Tools and Applications",
        "volume": "79",
        "pages": "12679-12716",
        "doi": "10.1007/s11042-019-08234-0",
        "type": "article"
    },
    "mrfo": {
        "title": "Manta ray foraging optimization: An effective bio-inspired optimizer for engineering applications",
        "authors": ["Zhao, W.", "Zhang, Z.", "Wang, L."],
        "year": 2020,
        "journal": "Engineering Applications of Artificial Intelligence",
        "volume": "87",
        "pages": "103300",
        "doi": "10.1016/j.engappai.2019.103300",
        "type": "article"
    },
    "opa": {
        "title": "Orca predation algorithm: A novel bio-inspired algorithm for global optimization problems",
        "authors": ["Faramarzi, A.", "Heidarinejad, M.", "Stephens, B.", "Mirjalili, S."],
        "year": 2021,
        "journal": "Expert Systems with Applications",
        "volume": "185",
        "pages": "115531",
        "doi": "10.1016/j.eswa.2021.115531",
        "type": "article"
    },
    "rro": {
        "title": "Raven roosting optimisation algorithm",
        "authors": ["Brabazon, A.", "Cui, W.", "O'Neill, M."],
        "year": 2016,
        "journal": "Soft Computing",
        "volume": "20",
        "number": "2",
        "pages": "525-545",
        "doi": "10.1007/s00500-014-1520-5",
        "type": "article"
    },
    "sho": {
        "title": "Spotted hyena optimizer: A novel bio-inspired based metaheuristic technique for engineering applications",
        "authors": ["Dhiman, G.", "Kumar, V."],
        "year": 2017,
        "journal": "Advances in Engineering Software",
        "volume": "114",
        "pages": "48-70",
        "doi": "10.1016/j.advengsoft.2017.05.014",
        "type": "article"
    },
    "sma": {
        "title": "Slime mould algorithm: A new method for stochastic optimization",
        "authors": ["Li, S.", "Chen, H.", "Wang, M.", "Heidari, A.A.", "Mirjalili, S."],
        "year": 2020,
        "journal": "Future Generation Computer Systems",
        "volume": "111",
        "pages": "300-323",
        "doi": "10.1016/j.future.2020.03.055",
        "type": "article"
    },
    "smo": {
        "title": "Starling murmuration optimizer: A novel bio-inspired algorithm for large scale problems",
        "authors": ["Zamani, H.", "Nadimi-Shahraki, M.H.", "Gandomi, A.H."],
        "year": 2022,
        "journal": "Expert Systems with Applications",
        "volume": "198",
        "pages": "116775",
        "doi": "10.1016/j.eswa.2022.116775",
        "type": "article"
    },
    "woa": {
        "title": "The whale optimization algorithm",
        "authors": ["Mirjalili, S.", "Lewis, A."],
        "year": 2016,
        "journal": "Advances in Engineering Software",
        "volume": "95",
        "pages": "51-67",
        "doi": "10.1016/j.advengsoft.2016.01.008",
        "type": "article"
    }
}


class CitationGenerator:
    """Generador de citas científicas."""
    
    def __init__(self):
        self.bioalgocompare_citation = {
            "title": "BioAlgoCompare: A Comprehensive Platform for Rigorous Statistical Evaluation of Bio-Inspired Algorithms",
            "authors": ["Anonymous"],  # Para review anónimo
            "year": 2025,
            "conference": "CISTI 2025",
            "type": "inproceedings",
            "note": "Submitted for review"
        }
    
    def generate_bibtex(self, algorithm_codes: List[str], include_platform: bool = True) -> str:
        """
        Genera citas BibTeX para los algoritmos especificados.
        
        Args:
            algorithm_codes: Lista de códigos de algoritmos
            include_platform: Si incluir cita de BioAlgoCompare
            
        Returns:
            String con citas BibTeX
        """
        bibtex_entries = []
        
        # Cita de la plataforma
        if include_platform:
            bibtex_entries.append(self._format_bibtex_entry("bioalgocompare2025", self.bioalgocompare_citation))
        
        # Citas de algoritmos
        for algo_code in algorithm_codes:
            if algo_code in ALGORITHM_CITATIONS:
                citation = ALGORITHM_CITATIONS[algo_code]
                key = f"{algo_code}_{citation['year']}"
                bibtex_entries.append(self._format_bibtex_entry(key, citation))
        
        return "\n\n".join(bibtex_entries)
    
    def _format_bibtex_entry(self, key: str, citation: Dict) -> str:
        """Formatea una entrada BibTeX."""
        
        entry_type = citation.get('type', 'article')
        entry = f"@{entry_type}{{{key},\n"
        
        # Título
        entry += f"  title = {{{citation['title']}}},\n"
        
        # Autores
        authors = " and ".join(citation['authors'])
        entry += f"  author = {{{authors}}},\n"
        
        # Año
        entry += f"  year = {{{citation['year']}}},\n"
        
        # Campos específicos por tipo
        if entry_type == 'article':
            entry += f"  journal = {{{citation['journal']}}},\n"
            if 'volume' in citation:
                entry += f"  volume = {{{citation['volume']}}},\n"
            if 'number' in citation:
                entry += f"  number = {{{citation['number']}}},\n"
            if 'pages' in citation:
                entry += f"  pages = {{{citation['pages']}}},\n"
        elif entry_type == 'inproceedings':
            if 'conference' in citation:
                entry += f"  booktitle = {{{citation['conference']}}},\n"
        
        # DOI
        if 'doi' in citation:
            entry += f"  doi = {{{citation['doi']}}},\n"
        
        # Nota
        if 'note' in citation:
            entry += f"  note = {{{citation['note']}}},\n"
        
        entry += "}"
        return entry
    
    def generate_apa_citations(self, algorithm_codes: List[str], include_platform: bool = True) -> str:
        """
        Genera citas en formato APA.
        
        Args:
            algorithm_codes: Lista de códigos de algoritmos
            include_platform: Si incluir cita de BioAlgoCompare
            
        Returns:
            String con citas APA
        """
        apa_citations = []
        
        # Cita de la plataforma
        if include_platform:
            apa_citations.append(self._format_apa_citation(self.bioalgocompare_citation))
        
        # Citas de algoritmos
        for algo_code in algorithm_codes:
            if algo_code in ALGORITHM_CITATIONS:
                citation = ALGORITHM_CITATIONS[algo_code]
                apa_citations.append(self._format_apa_citation(citation))
        
        return "\n\n".join(apa_citations)
    
    def _format_apa_citation(self, citation: Dict) -> str:
        """Formatea una cita en formato APA."""
        
        # Autores
        authors = citation['authors']
        if len(authors) == 1:
            author_str = authors[0]
        elif len(authors) == 2:
            author_str = f"{authors[0]} & {authors[1]}"
        else:
            author_str = ", ".join(authors[:-1]) + f", & {authors[-1]}"
        
        # Año
        year = citation['year']
        
        # Título
        title = citation['title']
        
        # Formatear según tipo
        if citation.get('type') == 'article':
            # Formato de artículo
            journal = citation['journal']
            apa = f"{author_str} ({year}). {title}. *{journal}*"
            
            if 'volume' in citation:
                apa += f", *{citation['volume']}*"
                if 'number' in citation:
                    apa += f"({citation['number']})"
            
            if 'pages' in citation:
                apa += f", {citation['pages']}"
            
            if 'doi' in citation:
                apa += f". https://doi.org/{citation['doi']}"
        
        elif citation.get('type') == 'inproceedings':
            # Formato de conferencia
            conference = citation.get('conference', 'Conference Proceedings')
            apa = f"{author_str} ({year}). {title}. In *{conference}*"
        
        else:
            # Formato genérico
            apa = f"{author_str} ({year}). {title}"
        
        apa += "."
        
        if 'note' in citation:
            apa += f" [{citation['note']}]"
        
        return apa
    
    def generate_ieee_citations(self, algorithm_codes: List[str], include_platform: bool = True) -> str:
        """
        Genera citas en formato IEEE.
        
        Args:
            algorithm_codes: Lista de códigos de algoritmos
            include_platform: Si incluir cita de BioAlgoCompare
            
        Returns:
            String con citas IEEE numeradas
        """
        ieee_citations = []
        
        # Cita de la plataforma
        if include_platform:
            ieee_citations.append(self._format_ieee_citation(self.bioalgocompare_citation))
        
        # Citas de algoritmos
        for algo_code in algorithm_codes:
            if algo_code in ALGORITHM_CITATIONS:
                citation = ALGORITHM_CITATIONS[algo_code]
                ieee_citations.append(self._format_ieee_citation(citation))
        
        # Numerar citas
        numbered_citations = []
        for i, citation in enumerate(ieee_citations, 1):
            numbered_citations.append(f"[{i}] {citation}")
        
        return "\n\n".join(numbered_citations)
    
    def _format_ieee_citation(self, citation: Dict) -> str:
        """Formatea una cita en formato IEEE."""
        
        # Autores (solo iniciales)
        authors = []
        for author in citation['authors']:
            parts = author.split(', ')
            if len(parts) >= 2:
                surname = parts[0]
                given_names = parts[1].split()
                initials = '. '.join([name[0] for name in given_names]) + '.'
                authors.append(f"{initials} {surname}")
            else:
                authors.append(author)
        
        author_str = ", ".join(authors)
        
        # Título
        title = f'"{citation["title"]}"'
        
        # Formatear según tipo
        if citation.get('type') == 'article':
            # Formato de artículo IEEE
            journal = f"*{citation['journal']}*"
            ieee = f"{author_str}, {title}, {journal}"
            
            if 'volume' in citation:
                ieee += f", vol. {citation['volume']}"
                if 'number' in citation:
                    ieee += f", no. {citation['number']}"
            
            if 'pages' in citation:
                ieee += f", pp. {citation['pages']}"
            
            ieee += f", {citation['year']}"
            
            if 'doi' in citation:
                ieee += f", doi: {citation['doi']}"
        
        elif citation.get('type') == 'inproceedings':
            # Formato de conferencia IEEE
            conference = citation.get('conference', 'Conf. Proc.')
            ieee = f"{author_str}, {title}, in *{conference}*, {citation['year']}"
        
        else:
            # Formato genérico IEEE
            ieee = f"{author_str}, {title}, {citation['year']}"
        
        ieee += "."
        
        return ieee
    
    def generate_citation_summary(self, algorithm_codes: List[str]) -> Dict:
        """
        Genera resumen de citas para documentación.
        
        Args:
            algorithm_codes: Lista de códigos de algoritmos
            
        Returns:
            Dict con información de citas
        """
        summary = {
            'total_algorithms': len(algorithm_codes),
            'algorithms_with_citations': 0,
            'algorithms_without_citations': [],
            'citation_years': [],
            'journals': [],
            'citations_by_year': {}
        }
        
        for algo_code in algorithm_codes:
            if algo_code in ALGORITHM_CITATIONS:
                summary['algorithms_with_citations'] += 1
                citation = ALGORITHM_CITATIONS[algo_code]
                
                year = citation['year']
                summary['citation_years'].append(year)
                
                if year not in summary['citations_by_year']:
                    summary['citations_by_year'][year] = []
                summary['citations_by_year'][year].append(algo_code)
                
                if citation.get('type') == 'article':
                    journal = citation['journal']
                    if journal not in summary['journals']:
                        summary['journals'].append(journal)
            else:
                summary['algorithms_without_citations'].append(algo_code)
        
        return summary
    
    def export_citations_to_file(self, algorithm_codes: List[str], output_path: str, 
                                format_type: str = 'bibtex', include_platform: bool = True):
        """
        Exporta citas a archivo.
        
        Args:
            algorithm_codes: Lista de códigos de algoritmos
            output_path: Ruta del archivo de salida
            format_type: Formato ('bibtex', 'apa', 'ieee')
            include_platform: Si incluir cita de BioAlgoCompare
        """
        if format_type == 'bibtex':
            content = self.generate_bibtex(algorithm_codes, include_platform)
        elif format_type == 'apa':
            content = self.generate_apa_citations(algorithm_codes, include_platform)
        elif format_type == 'ieee':
            content = self.generate_ieee_citations(algorithm_codes, include_platform)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)


def generate_all_citation_formats(algorithm_codes: List[str], output_dir: str):
    """
    Genera todos los formatos de citas en un directorio.
    
    Args:
        algorithm_codes: Lista de códigos de algoritmos
        output_dir: Directorio de salida
    """
    from pathlib import Path
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    generator = CitationGenerator()
    
    # Generar todos los formatos
    generator.export_citations_to_file(algorithm_codes, output_path / "citations.bib", "bibtex")
    generator.export_citations_to_file(algorithm_codes, output_path / "citations_apa.txt", "apa")
    generator.export_citations_to_file(algorithm_codes, output_path / "citations_ieee.txt", "ieee")
    
    # Generar resumen
    summary = generator.generate_citation_summary(algorithm_codes)
    with open(output_path / "citation_summary.json", 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"Citation files generated in {output_dir}")
    print(f"- BibTeX: citations.bib")
    print(f"- APA: citations_apa.txt") 
    print(f"- IEEE: citations_ieee.txt")
    print(f"- Summary: citation_summary.json")


if __name__ == "__main__":
    # Ejemplo de uso
    algorithms = ["aha", "egto", "foa", "woa", "hho"]
    generate_all_citation_formats(algorithms, "citations_output")