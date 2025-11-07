# -*- coding: utf-8 -*-
"""Procesador de documentos - Soporte para múltiples formatos incluyendo SVG"""

import os
import xml.etree.ElementTree as ET
from typing import List, Optional
from pathlib import Path
import re


class DocumentProcessor:
    """Procesador de documentos para extraer texto de diferentes formatos"""
    
    @staticmethod
    def extract_text_from_svg(svg_path: str) -> str:
        """
        Extrae texto y datos de un archivo SVG
        
        Extrae:
        - Texto de elementos <text> y <tspan>
        - Contenido de <metadata> y <desc>
        - Atributos relevantes como title, aria-label
        - Datos de elementos con atributos data-*
        """
        try:
            tree = ET.parse(svg_path)
            root = tree.getroot()
            
            # Namespace para SVG
            ns = {'svg': 'http://www.w3.org/2000/svg'}
            
            extracted_text = []
            
            # Extraer texto de elementos <text> y <tspan>
            for text_elem in root.findall('.//{http://www.w3.org/2000/svg}text', ns):
                text_content = (text_elem.text or '').strip()
                if text_content:
                    extracted_text.append(text_content)
            
            for tspan in root.findall('.//{http://www.w3.org/2000/svg}tspan', ns):
                tspan_content = (tspan.text or '').strip()
                if tspan_content:
                    extracted_text.append(tspan_content)
            
            # Extraer contenido de <metadata>
            for metadata in root.findall('.//{http://www.w3.org/2000/svg}metadata', ns):
                metadata_text = ET.tostring(metadata, encoding='unicode', method='text').strip()
                if metadata_text:
                    extracted_text.append(metadata_text)
            
            # Extraer contenido de <desc>
            for desc in root.findall('.//{http://www.w3.org/2000/svg}desc', ns):
                desc_text = (desc.text or '').strip()
                if desc_text:
                    extracted_text.append(desc_text)
            
            # Extraer atributos title y aria-label de todos los elementos
            for elem in root.iter():
                title = elem.get('title', '').strip()
                if title:
                    extracted_text.append(f"Título: {title}")
                
                aria_label = elem.get('aria-label', '').strip()
                if aria_label:
                    extracted_text.append(f"Etiqueta: {aria_label}")
                
                # Extraer atributos data-*
                for attr_name, attr_value in elem.attrib.items():
                    if attr_name.startswith('data-'):
                        extracted_text.append(f"{attr_name}: {attr_value}")
            
            # Extraer texto directo del SVG (sin namespace)
            for text_elem in root.findall('.//text'):
                text_content = (text_elem.text or '').strip()
                if text_content:
                    extracted_text.append(text_content)
            
            for tspan in root.findall('.//tspan'):
                tspan_content = (tspan.text or '').strip()
                if tspan_content:
                    extracted_text.append(tspan_content)
            
            # Combinar todo el texto extraído
            full_text = '\n'.join(extracted_text)
            
            # Si no se encontró texto, intentar extraer todo el contenido como texto plano
            if not full_text.strip():
                full_text = ET.tostring(root, encoding='unicode', method='text')
                # Limpiar espacios en blanco excesivos
                full_text = re.sub(r'\s+', ' ', full_text).strip()
            
            return full_text if full_text.strip() else ""
        
        except ET.ParseError as e:
            raise ValueError(f"Error al parsear el archivo SVG: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error al procesar el archivo SVG: {str(e)}")
    
    @staticmethod
    def process_file(file_path: str) -> str:
        """
        Procesa un archivo y extrae su contenido como texto
        
        Soporta:
        - Archivos de texto (.txt)
        - Archivos SVG (.svg)
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"El archivo no existe: {file_path}")
        
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == '.svg':
            return DocumentProcessor.extract_text_from_svg(file_path)
        elif file_ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            # Intentar leer como texto plano
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except UnicodeDecodeError:
                raise ValueError(f"Formato de archivo no soportado: {file_ext}. Se soportan .txt y .svg")
    
    @staticmethod
    def is_svg_file(file_path: str) -> bool:
        """Verifica si un archivo es SVG"""
        return Path(file_path).suffix.lower() == '.svg'
    
    @staticmethod
    def get_supported_extensions() -> List[str]:
        """Retorna las extensiones de archivo soportadas"""
        return ['.txt', '.svg']


