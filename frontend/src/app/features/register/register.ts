import { Component } from "@angular/core";
import { FormsModule } from "@angular/forms";
import { Router } from "@angular/router";

@Component({
  standalone: true,               // ✅ mark it as standalone
  selector: 'app-register-form',
  imports: [FormsModule],         // ✅ needed for [(ngModel)]
  template: `
    <h2>Enter your name to join</h2>
    <form (ngSubmit)="saveName()">
      <input
        type="text"
        [(ngModel)]="name"
        name="name"
        required
        placeholder="Your name"
      />
      <button type="submit">Continue</button>
    </form>
  `
})
export class RegisterComponent {
  name = '';

  constructor(private router: Router) {}

  saveName() {
    const trimmed = this.name.trim();
    if (!trimmed) return;

    // store as JSON with an id + name
    const visitor = {
      id: crypto.randomUUID(),
      name: trimmed
    };
    localStorage.setItem('visitor', JSON.stringify(visitor));

    this.router.navigate(['/lobby']);
  }
}
