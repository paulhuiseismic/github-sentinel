"""
仓库数据模型
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional, List


@dataclass
class Repository:
    """GitHub仓库模型"""
    id: int
    name: str
    full_name: str
    owner: str
    description: Optional[str]
    html_url: str
    stargazers_count: int = 0
    forks_count: int = 0
    open_issues_count: int = 0
    watchers_count: int = 0
    language: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    pushed_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Repository':
        """从GitHub API响应创建仓库对象"""
        # 处理时间字段
        def parse_datetime(date_str: Optional[str]) -> Optional[datetime]:
            if date_str:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return None

        return cls(
            id=data["id"],
            name=data["name"],
            full_name=data["full_name"],
            owner=data["owner"]["login"],
            description=data.get("description"),
            html_url=data["html_url"],
            stargazers_count=data.get("stargazers_count", 0),
            forks_count=data.get("forks_count", 0),
            open_issues_count=data.get("open_issues_count", 0),
            watchers_count=data.get("watchers_count", 0),
            language=data.get("language"),
            created_at=parse_datetime(data.get("created_at")),
            updated_at=parse_datetime(data.get("updated_at")),
            pushed_at=parse_datetime(data.get("pushed_at"))
        )


@dataclass
class RepositoryUpdate:
    """仓库更新记录"""
    repo_name: str
    owner: str
    update_type: str  # commits, issues, pull_requests, releases
    title: str
    description: Optional[str]
    url: str
    author: str
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'repo_name': self.repo_name,
            'owner': self.owner,
            'update_type': self.update_type,
            'title': self.title,
            'description': self.description,
            'url': self.url,
            'author': self.author,
            'created_at': self.created_at.isoformat(),
            'metadata': self.metadata
        }

    @classmethod
    def from_commit(cls, owner: str, repo_name: str, commit_data: Dict[str, Any]) -> 'RepositoryUpdate':
        """从commit数据创建更新记录"""
        commit = commit_data["commit"]
        return cls(
            repo_name=repo_name,
            owner=owner,
            update_type="commits",
            title=commit["message"].split('\n')[0][:100],  # 取第一行，限制长度
            description=commit["message"],
            url=commit_data["html_url"],
            author=commit["author"]["name"],
            created_at=datetime.fromisoformat(commit["author"]["date"].replace('Z', '+00:00')),
            metadata={"sha": commit_data["sha"]}
        )

    @classmethod
    def from_issue(cls, owner: str, repo_name: str, issue_data: Dict[str, Any]) -> 'RepositoryUpdate':
        """从issue数据创建更新记录"""
        return cls(
            repo_name=repo_name,
            owner=owner,
            update_type="issues",
            title=issue_data["title"],
            description=issue_data.get("body"),
            url=issue_data["html_url"],
            author=issue_data["user"]["login"],
            created_at=datetime.fromisoformat(issue_data["created_at"].replace('Z', '+00:00')),
            metadata={
                "number": issue_data["number"],
                "state": issue_data["state"],
                "labels": [label["name"] for label in issue_data.get("labels", [])]
            }
        )

    @classmethod
    def from_pull_request(cls, owner: str, repo_name: str, pr_data: Dict[str, Any]) -> 'RepositoryUpdate':
        """从PR数据创建更新记录"""
        return cls(
            repo_name=repo_name,
            owner=owner,
            update_type="pull_requests",
            title=pr_data["title"],
            description=pr_data.get("body"),
            url=pr_data["html_url"],
            author=pr_data["user"]["login"],
            created_at=datetime.fromisoformat(pr_data["created_at"].replace('Z', '+00:00')),
            metadata={
                "number": pr_data["number"],
                "state": pr_data["state"],
                "mergeable": pr_data.get("mergeable"),
                "base_branch": pr_data["base"]["ref"],
                "head_branch": pr_data["head"]["ref"]
            }
        )

    @classmethod
    def from_release(cls, owner: str, repo_name: str, release_data: Dict[str, Any]) -> 'RepositoryUpdate':
        """从release数据创建更新记录"""
        return cls(
            repo_name=repo_name,
            owner=owner,
            update_type="releases",
            title=release_data["name"] or release_data["tag_name"],
            description=release_data.get("body"),
            url=release_data["html_url"],
            author=release_data["author"]["login"],
            created_at=datetime.fromisoformat(release_data["created_at"].replace('Z', '+00:00')),
            metadata={
                "tag_name": release_data["tag_name"],
                "prerelease": release_data["prerelease"],
                "draft": release_data["draft"]
            }
        )
