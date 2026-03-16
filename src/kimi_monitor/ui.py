"""Rich UI components for Kimi Usage Monitor."""

from datetime import datetime
from typing import Optional, List

from rich.console import Console, Group
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, TaskProgressColumn
from rich.table import Table
from rich.text import Text
from rich.layout import Layout
from rich.live import Live
from rich.style import Style
from rich.theme import Theme

from .models import UsageData, DailyUsage, Config


class KimiTheme:
    """Kimi monitor color themes."""
    
    # Color definitions
    PRIMARY = "#667eea"
    SECONDARY = "#764ba2"
    SUCCESS = "#28a745"
    WARNING = "#ffc107"
    DANGER = "#dc3545"
    INFO = "#17a2b8"
    
    TEXT_LIGHT = "#f8f9fa"
    TEXT_DARK = "#212529"
    BG_LIGHT = "#ffffff"
    BG_DARK = "#1a1a2e"
    
    @classmethod
    def get_theme(cls, theme_name: str = "auto") -> Theme:
        """Get Rich theme.
        
        Args:
            theme_name: Theme name (auto, light, dark, classic)
            
        Returns:
            Rich Theme instance
        """
        if theme_name == "dark":
            return Theme({
                "info": cls.INFO,
                "success": cls.SUCCESS,
                "warning": cls.WARNING,
                "danger": cls.DANGER,
                "primary": cls.PRIMARY,
                "secondary": cls.SECONDARY,
            })
        elif theme_name == "classic":
            return Theme({
                "info": "cyan",
                "success": "green",
                "warning": "yellow",
                "danger": "red",
                "primary": "blue",
                "secondary": "magenta",
            })
        else:  # light or auto
            return Theme({
                "info": cls.INFO,
                "success": cls.SUCCESS,
                "warning": cls.WARNING,
                "danger": cls.DANGER,
                "primary": cls.PRIMARY,
                "secondary": cls.SECONDARY,
            })


class KimiUI:
    """Kimi Usage Monitor UI."""
    
    def __init__(self, config: Config):
        """Initialize UI.
        
        Args:
            config: Monitor configuration
        """
        self.config = config
        self.theme = KimiTheme.get_theme(config.theme)
        self.console = Console(theme=self.theme)
        self._live: Optional[Live] = None
    
    def _get_status_color(self, usage: UsageData) -> str:
        """Get color based on usage status.
        
        Args:
            usage: Usage data
            
        Returns:
            Color name
        """
        status = usage.status
        if status == "critical":
            return "danger"
        elif status == "warning":
            return "warning"
        return "success"
    
    def _format_number(self, num: int) -> str:
        """Format number with K/M suffix.
        
        Args:
            num: Number to format
            
        Returns:
            Formatted string
        """
        if num >= 1_000_000:
            return f"{num / 1_000_000:.2f}M"
        elif num >= 1_000:
            return f"{num / 1_000:.1f}K"
        return str(num)
    
    def _format_cost(self, cost: float) -> str:
        """Format cost.
        
        Args:
            cost: Cost value
            
        Returns:
            Formatted string
        """
        if cost >= 100:
            return f"${cost:.2f}"
        elif cost >= 1:
            return f"${cost:.3f}"
        return f"${cost:.4f}"
    
    def create_progress_bar(self, usage: UsageData) -> Progress:
        """Create usage progress bar.
        
        Args:
            usage: Usage data
            
        Returns:
            Progress widget
        """
        color = self._get_status_color(usage)
        
        progress = Progress(
            TextColumn("[bold]{task.description}"),
            BarColumn(
                complete_style=color,
                finished_style=color,
                pulse_style=color,
            ),
            TaskProgressColumn(),
            TextColumn("[dim]{task.fields[remaining]} remaining"),
            console=self.console,
            expand=True,
        )
        
        progress.add_task(
            "Token Usage",
            total=usage.total_quota,
            completed=usage.used_quota,
            remaining=self._format_number(usage.remaining_quota),
        )
        
        return progress
    
    def create_usage_table(self, usage: UsageData) -> Table:
        """Create usage statistics table.
        
        Args:
            usage: Usage data
            
        Returns:
            Table widget
        """
        table = Table(
            title="📊 Usage Statistics",
            box=None,
            show_header=True,
            header_style="bold blue",
        )
        
        table.add_column("Metric", style="dim")
        table.add_column("Value", justify="right")
        table.add_column("Percentage", justify="right")
        
        # Check if we have valid data / 檢查是否有有效資料
        if usage.total_quota == 0:
            table.add_row(
                "Status",
                "No usage data available / 無可用使用資料",
                "",
                style="warning",
            )
            table.add_row(
                "Note",
                "API may not support usage query / API 可能不支援使用查詢",
                "",
                style="dim",
            )
            return table
        
        # Total quota
        table.add_row(
            "Total Quota",
            self._format_number(usage.total_quota),
            "100%"
        )
        
        # Used
        table.add_row(
            "Used",
            self._format_number(usage.used_quota),
            f"{usage.usage_percentage:.1f}%",
            style="warning" if usage.usage_percentage > 70 else None,
        )
        
        # Remaining
        remaining_color = self._get_status_color(usage)
        table.add_row(
            "Remaining",
            self._format_number(usage.remaining_quota),
            f"{usage.remaining_percentage:.1f}%",
            style=remaining_color,
        )
        
        # Daily usage
        if usage.daily_usage > 0:
            table.add_row(
                "Today's Usage",
                self._format_number(usage.daily_usage),
                "",
            )
        
        # Weekly usage
        if usage.weekly_usage > 0:
            table.add_row(
                "This Week",
                self._format_number(usage.weekly_usage),
                "",
            )
        
        # Cost
        if self.config.show_cost and usage.total_cost > 0:
            table.add_row(
                "Total Cost",
                self._format_cost(usage.total_cost),
                "",
                style="info",
            )
        
        return table
    
    def create_plan_info(self, usage: UsageData) -> Panel:
        """Create plan information panel.
        
        Args:
            usage: Usage data
            
        Returns:
            Panel widget
        """
        content = []
        
        # Plan name
        content.append(f"[bold]Plan:[/bold] {usage.plan.upper()}")
        
        # Expiration
        if usage.expires_at:
            days = usage.days_until_expiry
            expiry_text = f"[bold]Expires:[/bold] {usage.expires_at.strftime('%Y-%m-%d')}"
            if days is not None:
                if days <= 7:
                    expiry_text += f" [danger]({days} days left)[/danger]"
                elif days <= 30:
                    expiry_text += f" [warning]({days} days left)[/warning]"
                else:
                    expiry_text += f" [success]({days} days left)[/success]"
            content.append(expiry_text)
        
        # Reset period
        content.append(f"[bold]Reset:[/bold] {usage.reset_period.capitalize()}")
        
        return Panel(
            "\n".join(content),
            title="📋 Plan Information",
            border_style="primary",
        )
    
    def create_daily_table(self, daily_data: List[DailyUsage]) -> Table:
        """Create daily usage table.
        
        Args:
            daily_data: List of daily usage
            
        Returns:
            Table widget
        """
        table = Table(
            title="📅 Daily Usage (Last 7 Days)",
            box=None,
            show_header=True,
            header_style="bold blue",
        )
        
        table.add_column("Date", style="dim")
        table.add_column("Tokens", justify="right")
        table.add_column("Requests", justify="right")
        table.add_column("Cost", justify="right")
        
        for day in daily_data:
            table.add_row(
                day.date.strftime("%Y-%m-%d"),
                self._format_number(day.total_tokens),
                str(day.request_count),
                self._format_cost(day.cost),
            )
        
        return table
    
    def create_main_layout(self, usage: UsageData, daily_data: Optional[List[DailyUsage]] = None) -> Layout:
        """Create main dashboard layout.
        
        Args:
            usage: Usage data
            daily_data: Optional daily usage history
            
        Returns:
            Layout widget
        """
        layout = Layout()
        
        # Split into sections
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3),
        )
        
        # Header
        header_text = Text("🌙 Kimi Usage Monitor", style="bold primary", justify="center")
        header_text.append("\n")
        header_text.append(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", style="dim")
        layout["header"].update(Panel(header_text, border_style="primary"))
        
        # Main content
        main_group = Group(
            self.create_progress_bar(usage),
            "",
            self.create_usage_table(usage),
            "",
            self.create_plan_info(usage),
        )
        
        if daily_data:
            main_group.renderables.extend(["", self.create_daily_table(daily_data)])
        
        layout["main"].update(Panel(main_group, border_style="secondary"))
        
        # Footer
        footer_text = Text("Press Ctrl+C to exit | ", style="dim")
        footer_text.append("Auto-refresh: ", style="dim")
        footer_text.append(f"{self.config.refresh_rate}s", style="info")
        layout["footer"].update(Panel(footer_text, border_style="dim"))
        
        return layout
    
    def print_error(self, message: str) -> None:
        """Print error message.
        
        Args:
            message: Error message
        """
        self.console.print(f"[danger]❌ Error:[/danger] {message}")
    
    def print_warning(self, message: str) -> None:
        """Print warning message.
        
        Args:
            message: Warning message
        """
        self.console.print(f"[warning]⚠️  Warning:[/warning] {message}")
    
    def print_success(self, message: str) -> None:
        """Print success message.
        
        Args:
            message: Success message
        """
        self.console.print(f"[success]✅ {message}[/success]")
    
    def print_info(self, message: str) -> None:
        """Print info message.
        
        Args:
            message: Info message
        """
        self.console.print(f"[info]ℹ️  {message}[/info]")
    
    def start_live(self, renderable) -> Live:
        """Start live display.
        
        Args:
            renderable: Renderable content
            
        Returns:
            Live instance
        """
        self._live = Live(
            renderable,
            console=self.console,
            refresh_per_second=self.config.refresh_per_second,
            screen=True,
        )
        self._live.start()
        return self._live
    
    def stop_live(self) -> None:
        """Stop live display."""
        if self._live:
            self._live.stop()
            self._live = None
    
    def update_live(self, renderable) -> None:
        """Update live display.
        
        Args:
            renderable: New renderable content
        """
        if self._live:
            self._live.update(renderable)
