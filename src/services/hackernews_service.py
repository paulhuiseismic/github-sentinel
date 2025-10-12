"""
Hacker News API 服务
"""
import aiohttp
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
import logging
import json
import re
from bs4 import BeautifulSoup

from ..models.hackernews import HackerNewsItem, HackerNewsUpdate


class HackerNewsService:
    """Hacker News API 服务类"""

    def __init__(self, timeout: int = 30):
        # 使用正确的Hacker News URL
        self.base_url = "https://news.ycombinator.com"
        self.api_url = "https://hacker-news.firebaseio.com/v0"
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.logger = logging.getLogger(__name__)
        self.session = None

    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()

    async def _get_session(self):
        """获取会话对象"""
        if self.session is None:
            self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self.session

    async def _make_request(self, url: str) -> Optional[Dict]:
        """发起HTTP请求获取JSON数据"""
        session = await self._get_session()
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    self.logger.error(f"请求失败: {url}, 状态码: {response.status}")
                    return None
        except Exception as e:
            self.logger.error(f"请求异常: {url}, 错误: {str(e)}")
            return None

    async def _make_html_request(self, url: str) -> Optional[str]:
        """发起HTTP请求获取HTML数据"""
        session = await self._get_session()
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    self.logger.error(f"HTML请求失败: {url}, 状态码: {response.status}")
                    return None
        except Exception as e:
            self.logger.error(f"HTML请求异常: {url}, 错误: {str(e)}")
            return None

    async def get_top_stories(self, limit: int = 30) -> List[int]:
        """获取热门故事ID列表"""
        url = f"{self.api_url}/topstories.json"
        story_ids = await self._make_request(url)
        if story_ids:
            return story_ids[:limit]
        return []

    async def get_new_stories(self, limit: int = 30) -> List[int]:
        """获取最新故事ID列表"""
        url = f"{self.api_url}/newstories.json"
        story_ids = await self._make_request(url)
        if story_ids:
            return story_ids[:limit]
        return []

    async def get_item(self, item_id: int) -> Optional[HackerNewsItem]:
        """获取单个项目详情"""
        url = f"{self.api_url}/item/{item_id}.json"
        item_data = await self._make_request(url)

        if not item_data:
            return None

        try:
            return HackerNewsItem(
                id=item_data.get('id'),
                title=item_data.get('title', ''),
                url=item_data.get('url', ''),
                score=item_data.get('score', 0),
                by=item_data.get('by', ''),
                time=datetime.fromtimestamp(item_data.get('time', 0), tz=timezone.utc),
                descendants=item_data.get('descendants', 0),
                type=item_data.get('type', 'story'),
                text=item_data.get('text', '')
            )
        except Exception as e:
            self.logger.error(f"解析项目数据失败: {item_id}, 错误: {str(e)}")
            return None

    async def get_stories_in_time_range(self,
                                      hours: int = 24,
                                      limit: int = 100,
                                      include_new: bool = True) -> List[HackerNewsItem]:
        """获取指定时间范围内的故事"""
        try:
            # 计算时间范围
            now = datetime.now(timezone.utc)
            since = now - timedelta(hours=hours)

            self.logger.info(f"获取过去{hours}小时内的Hacker News故事")

            stories = []

            # 获取热门故事
            top_story_ids = await self.get_top_stories(limit)
            if top_story_ids:
                top_tasks = [self.get_item(story_id) for story_id in top_story_ids]
                top_stories = await asyncio.gather(*top_tasks, return_exceptions=True)

                for story in top_stories:
                    if isinstance(story, HackerNewsItem) and story.time > since:
                        stories.append(story)

            # 如果需要，也获取最新故事
            if include_new:
                new_story_ids = await self.get_new_stories(limit)
                if new_story_ids:
                    new_tasks = [self.get_item(story_id) for story_id in new_story_ids]
                    new_stories = await asyncio.gather(*new_tasks, return_exceptions=True)

                    for story in new_stories:
                        if isinstance(story, HackerNewsItem) and story.time > since:
                            # 避免重复
                            if not any(s.id == story.id for s in stories):
                                stories.append(story)

            # 按分数排序，选择最热门的
            stories.sort(key=lambda x: x.score, reverse=True)

            self.logger.info(f"在过去{hours}小时内找到{len(stories)}个相关故事")
            return stories[:30]  # 限制返回数量

        except Exception as e:
            self.logger.error(f"获取时间范围内的故事失败: {str(e)}")
            return []

    async def get_front_page_stories(self) -> List[HackerNewsItem]:
        """通过爬取首页获取当前热门故事"""
        try:
            html = await self._make_html_request(f"{self.base_url}/")
            if not html:
                return []

            soup = BeautifulSoup(html, 'html.parser')
            story_links = soup.find_all('span', class_='titleline')

            stories = []
            for i, link_span in enumerate(story_links[:30]):  # 限制前30个
                try:
                    link = link_span.find('a')
                    if link:
                        title = link.get_text(strip=True)
                        url = link.get('href', '')

                        # 如果是相对链接，转换为绝对链接
                        if url.startswith('item?id='):
                            url = f"{self.base_url}/{url}"
                        elif url.startswith('/'):
                            url = f"{self.base_url}{url}"

                        # 创建简化的HackerNewsItem
                        story = HackerNewsItem(
                            id=i + 1,  # 临时ID
                            title=title,
                            url=url,
                            score=0,  # 需要额外解析才能获取分数
                            by='',
                            time=datetime.now(timezone.utc),
                            descendants=0,
                            type='story'
                        )
                        stories.append(story)

                except Exception as e:
                    self.logger.error(f"解析故事失败: {str(e)}")
                    continue

            self.logger.info(f"从首页获取到{len(stories)}个故事")
            return stories

        except Exception as e:
            self.logger.error(f"爬取首页失败: {str(e)}")
            return []

    async def get_top_stories_details(self, limit: int = 30) -> List[HackerNewsItem]:
        """获取热门故事详情列表"""
        story_ids = await self.get_top_stories(limit)
        if not story_ids:
            return []

        # 并发获取所有故事详情
        tasks = [self.get_item(story_id) for story_id in story_ids]
        stories = await asyncio.gather(*tasks, return_exceptions=True)

        # 过滤掉失败的请求和异常
        valid_stories = []
        for story in stories:
            if isinstance(story, HackerNewsItem):
                valid_stories.append(story)
            elif isinstance(story, Exception):
                self.logger.error(f"获取故事详情异常: {str(story)}")

        return valid_stories

    async def get_current_hot_topics(self, hours: int = 24) -> List[HackerNewsItem]:
        """获取当前热门话题（综合多种方式）"""
        try:
            # 方式1: 通过API获取时间范围内的故事
            api_stories = await self.get_stories_in_time_range(hours=hours)

            # 方式2: 获取当前热门故事作为补充
            top_stories = await self.get_top_stories_details(limit=30)

            # 合并并去重
            all_stories = {}

            # 添加API获取的故事
            for story in api_stories:
                all_stories[story.id] = story

            # 添加热门故事（如果不存在）
            for story in top_stories:
                if story.id not in all_stories:
                    all_stories[story.id] = story

            # 按分数排序
            final_stories = list(all_stories.values())
            final_stories.sort(key=lambda x: x.score, reverse=True)

            self.logger.info(f"获取到{len(final_stories)}个热门话题")
            return final_stories[:30]

        except Exception as e:
            self.logger.error(f"获取热门话题失败: {str(e)}")
            return []

    async def close(self):
        """关闭连接"""
        if self.session:
            await self.session.close()
            self.session = None
