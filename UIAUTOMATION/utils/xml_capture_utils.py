"""
界面 XML 自动采集工具
支持 Android/iOS 双平台，结构化存储 XML 文件
"""
import os
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Optional

from utils.log_utils import global_logger as logger


class XMLCaptureUtils:
    """界面 XML 自动采集工具"""

    # XML 存储根目录
    XML_ROOT_DIR = "data/page_xml"

    @staticmethod
    def ensure_dir_exists(file_path: str):
        """确保目录存在"""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

    @staticmethod
    def capture_page_source(
        driver,
        page_name: str,
        app_name: str = "main",
        platform: str = "android",
        description: str = "",
        auto_save: bool = True
    ) -> str:
        """
        采集当前界面 XML 并存储

        :param driver: Appium Driver 实例
        :param page_name: 页面名称（如 "home", "shelf", "reader"）
        :param app_name: 应用名称（main/vest1/vest2/vest3）
        :param platform: 平台（android/ios）
        :param description: 页面描述（可选，用于后续 AI 理解）
        :param auto_save: 是否自动保存到文件
        :return: XML 内容字符串
        """
        # 1. 获取页面源码
        xml_content = driver.page_source

        # 2. 生成文件名（带时间戳）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{page_name}_{timestamp}.xml"

        # 3. 构建存储路径：data/page_xml/{platform}/{app_name}/{page_name}/
        relative_path = f"{platform}/{app_name}/{page_name}/{filename}"
        full_path = os.path.join(XMLCaptureUtils.XML_ROOT_DIR, relative_path)

        # 4. 保存 XML 文件
        if auto_save:
            XMLCaptureUtils.ensure_dir_exists(full_path)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(xml_content)

            # 5. 同时保存元数据文件（便于后续 AI 分析）
            metadata_path = full_path.replace(".xml", "_meta.json")
            import json
            metadata = {
                "page_name": page_name,
                "app_name": app_name,
                "platform": platform,
                "timestamp": timestamp,
                "description": description,
                "xml_file": filename,
                "window_size": driver.get_window_size(),
            }
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            logger.info(f"✅ XML 已保存：{full_path}")
            logger.info(f"✅ 元数据已保存：{metadata_path}")

        return xml_content

    @staticmethod
    def extract_interactive_elements(xml_content: str) -> List[Dict]:
        """
        从 XML 中提取所有可交互元素

        :param xml_content: XML 内容字符串
        :return: 元素信息列表
        """
        elements = []
        try:
            root = ET.fromstring(xml_content)

            # 遍历所有节点
            for node in root.iter():
                # 提取关键属性
                attrs = {
                    "tag": node.tag,
                    "resource-id": node.attrib.get("resource-id", ""),
                    "text": node.attrib.get("text", ""),
                    "content-desc": node.attrib.get("content-desc", ""),
                    "class": node.attrib.get("class", ""),
                    "clickable": node.attrib.get("clickable", "false") == "true",
                    "bounds": node.attrib.get("bounds", ""),
                }

                # 只保留可交互或有意义的元素
                if (attrs["clickable"] or
                    attrs["text"] or
                    attrs["content-desc"] or
                    attrs["resource-id"]):
                    elements.append(attrs)

        except ET.ParseError as e:
            logger.error(f"XML 解析失败：{e}")

        return elements

    @staticmethod
    def generate_element_summary(elements: List[Dict]) -> str:
        """
        生成元素摘要（便于快速查看）

        :param elements: 元素列表
        :return: 摘要字符串
        """
        summary = []
        summary.append(f"共找到 {len(elements)} 个可交互元素：\n")

        for i, elem in enumerate(elements, 1):
            summary.append(f"{i}. [{elem['tag']}]")
            if elem['resource-id']:
                summary.append(f"   id: {elem['resource-id']}")
            if elem['text']:
                summary.append(f"   text: {elem['text']}")
            if elem['content-desc']:
                summary.append(f"   desc: {elem['content-desc']}")
            summary.append(f"   clickable: {elem['clickable']}")
            summary.append("")

        return "\n".join(summary)

    @staticmethod
    def list_captured_pages(
        platform: str = "android",
        app_name: str = "main"
    ) -> List[str]:
        """
        列出已采集的页面

        :return: 页面名称列表
        """
        base_dir = os.path.join(XMLCaptureUtils.XML_ROOT_DIR, platform, app_name)
        if not os.path.exists(base_dir):
            return []

        pages = []
        for page_name in os.listdir(base_dir):
            page_path = os.path.join(base_dir, page_name)
            if os.path.isdir(page_path):
                # 统计该页面有多少个 XML 文件
                xml_files = [f for f in os.listdir(page_path) if f.endswith(".xml") and not f.endswith("_meta.json")]
                pages.append(f"{page_name} ({len(xml_files)} 个文件)")

        return pages
