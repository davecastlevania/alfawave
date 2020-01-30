import factory

from funkwhale_api.factories import registry, NoUpdateOnCreate
from funkwhale_api.federation import factories as federation_factories
from funkwhale_api.music import factories as music_factories

from . import models


def set_actor(o):
    return models.generate_actor(str(o.uuid))


@registry.register
class ChannelFactory(NoUpdateOnCreate, factory.django.DjangoModelFactory):
    uuid = factory.Faker("uuid4")
    attributed_to = factory.SubFactory(federation_factories.ActorFactory)
    library = factory.SubFactory(
        federation_factories.MusicLibraryFactory,
        actor=factory.SelfAttribute("..attributed_to"),
        privacy_level="everyone",
    )
    actor = factory.LazyAttribute(set_actor)
    artist = factory.SubFactory(
        music_factories.ArtistFactory,
        attributed_to=factory.SelfAttribute("..attributed_to"),
    )

    class Meta:
        model = "audio.Channel"

    class Params:
        local = factory.Trait(
            attributed_to=factory.SubFactory(
                federation_factories.ActorFactory, local=True
            ),
            artist__local=True,
        )


@registry.register(name="audio.Subscription")
class SubscriptionFactory(NoUpdateOnCreate, factory.django.DjangoModelFactory):
    uuid = factory.Faker("uuid4")
    approved = True
    target = factory.LazyAttribute(lambda o: ChannelFactory().actor)
    actor = factory.SubFactory(federation_factories.ActorFactory)

    class Meta:
        model = "federation.Follow"
