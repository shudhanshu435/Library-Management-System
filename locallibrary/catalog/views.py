from django.shortcuts import render

# Create your views here.
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Book, Author, BookInstance, Genre, Language, BorrowHistory
import datetime
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required, permission_required
from catalog.forms import RenewBookForm

def index(request):
    """View function for home page of site."""

    # calculate counts for genres and books containing a particular word
    word = "one"
    num_books_with_word = Book.objects.filter(title__icontains=word).count()
    num_genres_with_word = Genre.objects.filter(name__icontains=word).count()

    # Generate counts of some of the main objects
    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()

    # Available books (status = 'a')
    num_instances_available = BookInstance.objects.filter(status__exact='a').count()

    # The 'all()' is implied by default.
    num_authors = Author.objects.count()

    num_visits = request.session.get('num_visits',1)
    request.session['num_visits'] = num_visits + 1

    context = {
        'num_books': num_books,
        'num_instances': num_instances,
        'num_instances_available': num_instances_available,
        'num_authors': num_authors,
        'num_books_with_word': num_books_with_word,
        'num_genres_with_word': num_genres_with_word,
        'num_visits': num_visits,
    }

    # Render the HTML template index.html with the data in the context variable
    return render(
        request,
        'index.html',
        context=context)


from django.views import generic
from django.db.models import Count, Q

class BookListView(generic.ListView):
    """Generic class based view for a list of books"""
    model = Book
    paginate_by = 10

    def get_queryset(self):
        queryset = Book.objects.annotate(
            total_copies=Count('bookinstance'),  # Counts all instances of the book
            available_copies=Count('bookinstance', filter=Q(bookinstance__status='a'))
        )
        return queryset


class BookDetailView(generic.DetailView):
    """Generic class based detail view for a book"""
    model = Book

    def get_queryset(self):
        queryset = Book.objects.annotate(
            total_copies=Count('bookinstance'),  # Counts all instances of the book
            available_copies=Count('bookinstance', filter=Q(bookinstance__status='a'))
        )
        return queryset


def book_detail_view(request, primary_key):
    try:
        book = Book.objects.get(pk=primary_key)
    except Book.DoesNotExist:
        raise Http404('Book does not exist')

    return render(request, 'catalog/book_detail.html', context={'book': book})


class AuthorListView(generic.ListView):
    model = Author
    paginate_by = 10

class AuthorDetailView(generic.DetailView):
    model = Author

def author_detail_view(request, primary_key):
    try:
        author = Author.objects.get(pk=primary_key)
    except Author.DoesNotExist:
        raise Http404('Author does not exist')

    return render(request, 'catalog/author_detail.html', context={'author': author})


class GenreDetailView(generic.DetailView):
    """Generic class-based detail view for a genre."""
    model = Genre

class GenreListView(generic.ListView):
    """Generic class-based list view for a list of genres."""
    model = Genre
    paginate_by = 10

class LanguageDetailView(generic.DetailView):
    """Generic class-based detail view for a genre."""
    model = Language

class LanguageListView(generic.ListView):
    """Generic class-based list view for a list of genres."""
    model = Language
    paginate_by = 10
class BookInstanceListView(generic.ListView):
    """Generic class-based view for a list of books."""
    model = BookInstance
    paginate_by = 10

class BookInstanceDetailView(generic.DetailView):
    """Generic class-based detail view for a book."""
    model = BookInstance

from django.contrib.auth.mixins import LoginRequiredMixin

class LoanedBooksByUserListView(LoginRequiredMixin, generic.ListView):
    """Generic class-based view listing books on loan to current user."""
    model = BookInstance
    template_name = 'catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 10

    def get_queryset(self):
        return (
            BookInstance.objects.filter(borrower=self.request.user)
            .filter(status__exact='o')
            .order_by('due_back')
        )

# Added as a part of challenge
from django.contrib.auth.mixins import PermissionRequiredMixin
# from django.views.generic import TemplateView

class LoanedBooksAllListView(PermissionRequiredMixin, generic.ListView):
    """Generic class based view listing all books on loan. Only visible to users with can_mark_returned permission."""
    model = BookInstance
    permission_required = 'catalog.can_mark_returned'
    template_name = 'catalog/bookinstance_list_borrowed_all.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(status__exact='o').order_by('due_back')


@login_required
@permission_required('catalog.can_mark_returned', raise_exception=True)
def renew_book_librarian(request, pk):
    book_instance = get_object_or_404(BookInstance, pk=pk)

    # If this is a POST request then process the Form data
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = RenewBookForm(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required (here we just write it to the model due_back field)
            book_instance.due_back = form.cleaned_data['renewal_date']
            book_instance.save()

            # redirect to a new URL:
            return HttpResponseRedirect(reverse('all-borrowed'))

    # If this is a GET (or any other method) create the default form.
    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={'renewal_date': proposed_renewal_date})

    context = {
        'form': form,
        'book_instance': book_instance,
    }

    return render(request, 'catalog/book_renew_librarian.html', context)


@login_required
def borrow_book_for_user(request):
    if request.method == 'POST':
        book_id = request.POST['book_id']
        user_id = request.POST['user_id']

        book_instance = get_object_or_404(BookInstance, id=book_id)
        user = get_object_or_404(User, id=user_id)

        # Now check if book is available for borrowing
        if book_instance.status == 'a' and book_instance.book.quantity > 0:
            BorrowHistory.objects.create(
                user=user,
                book=book_instance.book,
                action='borrow'
            )
            book_instance.status = 'o'  # on loan
            book_instance.borrower = user

            # Set due_back date (e.g., 2 weeks from now)
            due_back_date = datetime.date.today() + datetime.timedelta(weeks=3)
            book_instance.due_back = due_back_date

            # Save changes to BookInstance
            book_instance.save()

            book_instance.book.quantity -= 1
            book_instance.book.save()

            return render(request, 'catalog/success.html')
        else:
            return render(request, 'catalog/error.html', {'message': 'Book not available'})

    available_books = BookInstance.objects.filter(status='a', book__quantity__gt=0)
    users = User.objects.all()

    return render(request, 'catalog/librarian_borrow_book.html', {
        'available_books': available_books,
        'users': users,
    })


@login_required
def return_book(request):
    if request.method == 'POST':
        book_id = request.POST['book_id']
        book_instance = get_object_or_404(BookInstance, id=book_id)

        # Check if the book is currently borrowed
        if book_instance.status == 'o':  # Assuming 'b' means borrowed
            # Update BookInstance status to available
            book_instance.status = 'a'  # Assuming 'o' means available
            borrower_user = book_instance.borrower  # Store the borrower before clearing it
            book_instance.borrower = None  # Clear the borrower field

            # Increase the quantity of the book by 1
            book_instance.book.quantity += 1

            # Save changes to both BookInstance and Book models
            book_instance.save()
            book_instance.book.save()

            # Log the return action in BorrowingHistory
            BorrowHistory.objects.create(
                user=borrower_user,
                book=book_instance.book,
                action='return',
                return_date=datetime.date.today()  # Set today's date as return date
            )

            return render(request, 'catalog/success.html')  # Redirect to a success page or back to list

        else:
            return render(request, 'catalog/error.html', {'message': 'This book is not currently borrowed.'})

    # For GET request: Show currently borrowed books for returning
    borrowed_books = BookInstance.objects.filter(status='o')

    return render(request, 'catalog/librarian_return_book.html', {
        'borrowed_books': borrowed_books,
    })


from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Author

class AuthorCreate(PermissionRequiredMixin, CreateView):
    model = Author
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']
    initial = {'date_of_death': '11/11/2023'}
    permission_required = 'catalog.add_author'

class AuthorUpdate(PermissionRequiredMixin, UpdateView):
    model = Author
    # Not recommended (potential security issue if more fields added)
    fields = '__all__'
    permission_required = 'catalog.change_author'

class AuthorDelete(PermissionRequiredMixin, DeleteView):
    model = Author
    success_url = reverse_lazy('authors')
    permission_required = 'catalog.delete_author'

    def form_valid(self, form):
        try:
            self.object.delete()
            return HttpResponseRedirect(self.success_url)
        except Exception as e:
            return HttpResponseRedirect(
                reverse("author-delete", kwargs={"pk": self.object.pk})
            )

class BookCreate(PermissionRequiredMixin, CreateView):
    model = Book
    fields = ['title', 'author', 'summary', 'isbn', 'genre', 'language']
    permission_required = 'catalog.add_book'


class BookUpdate(PermissionRequiredMixin, UpdateView):
    model = Book
    fields = ['title', 'author', 'summary', 'isbn', 'genre', 'language']
    permission_required = 'catalog.change_book'


class BookDelete(PermissionRequiredMixin, DeleteView):
    model = Book
    success_url = reverse_lazy('books')
    permission_required = 'catalog.delete_book'

    def form_valid(self, form):
        try:
            self.object.delete()
            return HttpResponseRedirect(self.success_url)
        except Exception as e:
            return HttpResponseRedirect(
                reverse("book-delete", kwargs={"pk": self.object.pk})
            )


class GenreCreate(PermissionRequiredMixin, CreateView):
    model = Genre
    fields = ['name', ]
    permission_required = 'catalog.add_genre'


class GenreUpdate(PermissionRequiredMixin, UpdateView):
    model = Genre
    fields = ['name', ]
    permission_required = 'catalog.change_genre'


class GenreDelete(PermissionRequiredMixin, DeleteView):
    model = Genre
    success_url = reverse_lazy('genres')
    permission_required = 'catalog.delete_genre'


class LanguageCreate(PermissionRequiredMixin, CreateView):
    model = Language
    fields = ['name', ]
    permission_required = 'catalog.add_language'


class LanguageUpdate(PermissionRequiredMixin, UpdateView):
    model = Language
    fields = ['name', ]
    permission_required = 'catalog.change_language'


class LanguageDelete(PermissionRequiredMixin, DeleteView):
    model = Language
    success_url = reverse_lazy('languages')
    permission_required = 'catalog.delete_language'
class BookInstanceCreate(PermissionRequiredMixin, CreateView):
    model = BookInstance
    fields = ['book', 'imprint', 'due_back', 'borrower', 'status']
    permission_required = 'catalog.add_bookinstance'


class BookInstanceUpdate(PermissionRequiredMixin, UpdateView):
    model = BookInstance
    # fields = "__all__"
    fields = ['imprint', 'due_back', 'borrower', 'status']
    permission_required = 'catalog.change_bookinstance'


class BookInstanceDelete(PermissionRequiredMixin, DeleteView):
    model = BookInstance
    success_url = reverse_lazy('bookinstances')
    permission_required = 'catalog.delete_bookinstance'



from django.shortcuts import render
from .forms import ContactForm
from .models import ContactMessage  # Assuming you have a ContactMessage model


def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Save the form data to the database
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            message = form.cleaned_data['message']
            contact_message = ContactMessage.objects.create(name=name, email=email, message=message)

            # Optionally, you can do additional processing here
            # For example, sending an email notification

            return render(request, 'success.html')  # Render a success page after submission
    else:
        form = ContactForm()

    return render(request, 'index.html', {'form': form})


from django.contrib.auth import logout
from django.shortcuts import redirect
from .forms import CustomerUserCreationForm
def register(request):
    if request.method == 'POST':
        form = CustomerUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Registered successfully.')
            return redirect('login')  # Redirect to login page after successful registration
    else:
        form = CustomerUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


def logout_view(request):
    logout(request)
    return render(request, 'registration/logged_out.html')  # Redirect to the home page after logout

def search(request):
    query = request.GET.get('query')
    if query:
        results = Book.objects.filter(title__icontains=query)
    else:
        results = None
    return render(request, 'search_results.html', {'results': results, 'query': query})


from django.db.models import Q
def search_author(request):
    query = request.GET.get('query')
    if query:
        results1 = Author.objects.filter(Q(first_name__icontains=query) | Q(last_name__icontains=query))

    else:
        results1 = None
    return render(request, 'search_authors.html', {'results1': results1, 'query': query})