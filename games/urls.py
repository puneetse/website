from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('games.views',
    url(r'^$', 'games_all'),
    #url(r'^genre/(?P<genre_slug>[\w\-]+$)', views.games_by_genre),
    #url(r'^year/(?P<year>[\d]+)$', views.games_by_year),
    #url(r'^runner/(?P<runner_slug>[\w\-]+)$', views.games_by_runner),
    #url(r'^developer/(?P<developer_slug>[\w\-]+)$', views.games_by_developer),
    #url(r'^publisher/(?P<publihser_slug>[\w\-]+)$', views.games_by_publisher),
    #url(r'^platform/(?P<platform_slug>[\w\-]+)$', views.games_by_platform),
    url(r'(?P<slug>[\w\-]+)$', "game_detail", name="game_detail"),
)
